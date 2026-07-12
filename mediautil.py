import json
import shutil
import pathlib
import functools
import mimetypes
import itertools
import collections
import dataclasses
from typing import Optional

from clldutils.path import md5
from clldutils.html import HTML, literal
from clldutils.misc import data_url
from clldutils.jsonlib import load
from csvw.metadata import URITemplate
from pycldf.sources import Reference


@dataclasses.dataclass(frozen=True)
class TocEntry:
    label: str
    href: str

    def html(self, directory: str):
       return HTML.li(HTML.a(self.label, href=f'{directory}/{self.href}'))


@dataclasses.dataclass
class TableOfContents:
    survey: collections.OrderedDict[str, list[TocEntry]] = dataclasses.field(
        default_factory=collections.OrderedDict)
    atlas: list[TocEntry] = dataclasses.field(default_factory=list)

    def add_survey(self, survey, fname):
        if survey['description'] not in self.survey:  # A new volume
            self.survey[survey['description']] = []
        self.survey[survey['description']].append(TocEntry(survey['name'], fname))

    def add_atlas_chapter(self, chapter, fname):
        self.atlas.append(TocEntry(chapter['name'], fname))

    def write(self, path: pathlib.Path):
        sindex = []
        for vol, items in self.survey.items():
            sindex.append(HTML.h3(vol))
            sindex.append(HTML.ul(*[item.html('Survey') for item in items]))
        path.write_text(html_doc(
            [HTML.title('APiCS')],
            [HTML.h1('APiCS'),
             HTML.h2('The Atlas of Pidgin and Creole Language Structures'),
             HTML.ol(*[item.html('Atlas') for item in self.atlas]),
             HTML.h2('The survey of pidgin and creole languages')] + sindex,
        ), encoding='utf8')


@dataclasses.dataclass
class LanguageContribution:
    lid: str
    survey: Optional[dict]
    structdataset: dict

    def structuredataset_as_contribution(self, obj, eds, lname):
        obj.update({
            'ID': self.lid,
            'type': 'StructureDataset',
            'Name': f'{lname} structure dataset',
            'Language_IDs': [self.lid],
        })
        obj['Citation'] = \
            "{Contributor}. 2013. {Name}. In: {eds} (eds.) Atlas of Pidgin and Creole Language " \
            "Structures Online. Leipzig: Max Planck Institute for Evolutionary Anthropology. " \
            "(Available online at https://apics-online.info/contributions/{ID} " \
            "Accessed on [DATE].)".format(eds=eds, **obj)
        return obj

    def survey_lids(self):
        return [self.lid, '51'] if int(self.lid) == 50 else [self.lid]

    def survey_as_contribution(self, obj, eds):
        obj.update({
            'ID': f's-{self.lid}',
            'type': "SurveyChapter",
            'Name': '{}. In "The survey of pidgin and creole languages". {}'.format(
                self.survey['name'], self.survey['description']),
            'Language_IDs': self.survey_lids(),
        })
        obj['Citation'] = \
            "{Contributor}. 2013. {Title}. In: {eds} (eds.) The survey of pidgin " \
            "and creole languages. {vol}. Oxford: Oxford University Press.".format(
                eds=eds, vol=self.survey['description'], Title=self.survey['name'], **obj)
        return obj

    def add_glossed_text(self, media, file_getter, lname):
        gt_audio, gt_pdf = None, None
        if self.structdataset:
            for f in self.structdataset.get('files', []):
                src, _ = file_getter(f)
                if src.suffix == '.pdf':
                    desc = 'PDF of glossed text for {}'.format(lname)
                    gt_pdf = src.name
                else:
                    assert src.suffix == '.mp3'
                    desc = 'Audio of the glossed text for {} being spoken'.format(lname)
                    gt_audio = src.name
                media.add(src, desc, dest='Survey', cid=f's-{self.lid}', lids=[self.lid])
        return gt_audio, gt_pdf


@dataclasses.dataclass
class LanguageContributions:
    """Keyed by id."""
    surveys: dict[str, dict]
    structdatasets: dict[str, dict]

    @classmethod
    def from_surveys_and_contribs(cls, surveys, contribs):
        surveys = {c['id']: c for c in surveys.values()}
        surveys['51'] = surveys['50']
        return cls(surveys, {c['id']: c for c in contribs.values()})

    def contributions(self, lid):
        return LanguageContribution(lid, self.surveys.get(lid), self.structdatasets.get(lid))


@dataclasses.dataclass
class LanguageMetadata:
    """Dicts, keyed by language/contribution pk to look up additional metadata."""
    data: dict[str, collections.OrderedDict[str, str]]
    refs: dict[str, set[str]]
    identifier: dict[str, dict[str, list[str]]]
    pk2id: dict[str, str] = dataclasses.field(default_factory=dict)

    @classmethod
    def from_csv(cls, reader, pk2id):
        ldata = {}
        for lpk, rows in itertools.groupby(
            reader('language_data', key=lambda d: (d['object_pk'], int(d['ord']))).values(),
            lambda d: d['object_pk'],
        ):
            ldata[lpk] = collections.OrderedDict([(d['key'], d['value']) for d in rows])

        lrefs = {
            lpk: set(pk2id['source'][r['source_pk']] for r in rows)
            for lpk, rows in itertools.groupby(
                reader('languagesource', key=lambda d: d['language_pk']).values(),
                lambda d: d['language_pk'])}
        for row in reader('contributionreference').values():
            lrefs[row['contribution_pk']].add(pk2id['source'][row['source_pk']])

        identifier = reader('identifier')
        lang2id = collections.defaultdict(lambda: collections.defaultdict(list))
        for row in reader('languageidentifier').values():
            id_ = identifier[row['identifier_pk']]
            lang2id[row['language_pk']][id_['type']].append((id_['name'], id_['description']))

        return cls(ldata, lrefs, lang2id)

    def update(self, d, lpk):
        """Update a language object with the additional metadata."""
        iso_codes = set(i[0] for i in self.identifier[lpk].get('iso639-3', []))
        glottocodes = [i[0] for i in self.identifier[lpk].get('glottolog', [])]
        ethnologue_names = [i[0] for i in self.identifier[lpk].get('ethnologue', [])]

        d.update({
            'ISO639P3code': list(iso_codes)[0] if len(iso_codes) == 1 else None,
            'Glottocode': glottocodes[0] if len(glottocodes) == 1 else None,
            'Ethnologue_Name': ', '.join(ethnologue_names),
            'Source': [str(Reference(r, None)) for r in sorted(self.refs.get(lpk, []))],
            'Metadata': json.dumps(self.data.get(lpk, {})),
        })
        return d


@dataclasses.dataclass
class Contributors:
    editors: dict[str, int]
    cnames: dict[str, str]
    contributors: list[dict]
    cc_ids: dict[str, list[str]]
    sc_ids: dict[str, list[str]]
    fc_ids: dict[str, list[str]]

    @functools.cached_property
    def editor_names(self):
        return ' & '.join(f"{n.split()[-1]}, {' '.join(n.split()[:-1])}" for n in self.editors)

    @classmethod
    def from_contrib_rows(
            cls,
            rows,
            cc,
            sc,
            fc,
    ):
        editors = {
            name: ord for ord, name in enumerate([
                'Susanne Maria Michaelis', 'Philippe Maurer', 'Martin Haspelmath', 'Magnus Huber',
            ], start=1)}

        cnames = {}
        contributors = []
        for row in rows:
            cnames[row['id']] = row['name']

            contributors.append({
                'ID': row['id'],
                'Name': row['name'],
                'Address': row['address'],
                'URL': row['url'],
                'editor_ord': editors.get(row['name']),
            })
        return cls(editors, cnames, contributors, cc, sc, fc)

    def concat(self, cids):
        if len(cids) < 3:
            return ' and '.join(self.cnames[cid] for cid in cids)
        return f"{', '.join(self.cnames[cid] for cid in cids[:-1])} and {self.cnames[cids[-1]]}"

    def contrib_spec(self, cids):
        """A Contribution object dict seeeded with the keys specifying contributors."""
        return dict(Contributor=self.concat(cids), Contributor_IDs=cids)


@dataclasses.dataclass
class MediaTable:
    fname2objid: dict[str, str]
    objects: dict[str, list]
    cldf_dir: pathlib.Path

    @classmethod
    def from_cdstar(cls, objects, cldf_dir, cdstar):
        res = {}
        for oid, md in cdstar.items():
            for bs in md['bitstreams']:
                assert bs['bitstreamid'] not in res
                #
                # FIXME: make sure we have this in s3!
                #
                res[bs['bitstreamid']] = oid
        return cls(res, objects, cldf_dir)

    def schema(self, cldf):
        cldf.add_component(
            'MediaTable',
            {
                'name': 'Contribution_ID',
                'propertyUrl': "http://cldf.clld.org/v1.0/terms.rdf#contributionReference",
                'dc:description': "Links to the contribution which contributed the media object."
            },
            {
                'name': 'Language_IDs',
                'propertyUrl': "http://cldf.clld.org/v1.0/terms.rdf#languageReference",
                'separator': ' ',
                'dc:description': "Links to languages described by the media object."
            },
            {'name': 'size', 'datatype': 'integer'},
            {
                'name': 'File_Key',
                'valueUrl': 'https://s3.nexus.mpcdf.mpg.de/eva-dlce-apics/{File_Key}'
            },
        )
        cldf.remove_columns('MediaTable', 'Name', 'Path_In_Zip')

    def add(
            self,
            src: pathlib.Path,
            description: str,
            dest=None,
            cid=None,
            lids=None,
            md5sum: Optional[str] = None,
    ):
        if md5sum:  # Check, if we already have the file.
            for f in self.objects['MediaTable']:
                if f['ID'] == md5sum:
                    if lids:
                        assert f['Language_IDs'] == lids
                    return

        assert src.exists()
        self.objects['MediaTable'].append({
            'ID': md5(src),
            'Description': description,
            'Media_Type': mimetypes.guess_type(src.name)[0],
            'Download_URL': '/'.join([dest, src.name]) if dest else str(src.relative_to(self.cldf_dir)),
            'size': src.stat().st_size,
            'Contribution_ID': cid,
            'Language_IDs': lids or [],
            'File_Key': f'{self.fname2objid.get(src.name)}_{src.name}' if src.name in self.fname2objid else None,
        })
        if dest:
            shutil.copy(src, self.cldf_dir / dest / src.name)


def get_text(p):
    from bs4 import BeautifulSoup as bs
    text = p.read_text(encoding='utf8')
    body = bs(text, 'html5lib').find('body')
    body.name = 'div'
    body.attrs.clear()
    body.attrs['id'] = 'raw-content'
    return f'{body}'.replace('.popover(', '.clickover(')


def html_doc(head, body):
    if isinstance(head, list):
        head = HTML.head(HTML.meta(charset="utf-8"), *head)
    if isinstance(body, list):
        body = HTML.body(*body)
    return "<!DOCTYPE html>\n{}".format(HTML.html(head, body, lang="en", dir="ltr"))


def contribution_media(etc, directory, sid, title=None, author=None, extra_section=None):
    html_p = directory / f'{sid}.html'
    html = get_text(html_p)
    maps = []
    for fname in sorted(directory.glob('%s-*.png' % sid), key=lambda p: p.stem):
        if 'figure' in fname.stem:
            data_uri = data_url(fname, 'image/png')
            html = html.replace('{%s}' % fname.name, '%s' % data_uri)
        else:
            maps.append(fname)

    md = load(directory / '{}.json'.format(sid))
    if title:
        md['title'] = title

    #
    # FIXME: turn into CLDF markdown? or at least use CLDF markdown-like URL to link to other objects?
    #
    before, after = [HTML.h1(md['title'], id='top')], []
    before.append(HTML.p('by ' + (author if author else ' and '.join(n['name'] for n in md['authors']))))
    hasrefs = False
    if md.get('refs') or md.get('refs_comments'):
        hasrefs = True
        after.append(HTML.h2('References', id='section-references'))
        if md.get('refs_comments'):
            for line in md['refs_comments']:
                after.append(HTML.p(literal(line)))
        count = 0
        for cat, refs in itertools.groupby(
                sorted(md.get('refs', []), key=lambda r: (r['category'] or '', r['key'] or '')),
                lambda r: r['category']
        ):
            refs = list(refs)
            if cat:
                after.append(HTML.h3(cat))
            after.append(HTML.ol(
                *[HTML.li(ref['text'], id=ref['id']) for ref in refs],
                **dict(class_='refs', start=str(count + 1))))
            count += len(refs)

    if md.get('outline'):
        lis = []
        for title, id_ in md['outline']:
            lis.append(HTML.li(HTML.a(title, href="#" + id_)))
        if hasrefs:
            lis.append(HTML.li(HTML.a('References', href="#section-references")))
        before.append(HTML.div(
            HTML.h2('Contents'),
            HTML.ol(*lis, **dict(class_='toc')),
            id='section-toc'))

    if maps:
        before.append(HTML.div(
            *[HTML.img(src='{}'.format(map.name)) for map in maps],
            **dict(id='section-maps')))
    before.append(HTML.hr(style='clear: both;'))

    if extra_section:
        before.append(extra_section)

    return html_doc(
        [
            HTML.title(md['title']),
            HTML.style(etc.joinpath('project.css').read_text(encoding='utf8')),
            HTML.style(directory.joinpath(f'{sid}.css').read_text(encoding='utf8')),
        ],
        before + [literal(str(html))] + after
    ), maps
