import json
import typing
import pathlib
import operator
import functools
import itertools
import collections
import urllib.request

from clldutils.path import md5
from clldutils.html import HTML
from clldutils.jsonlib import load
from cldfbench import Dataset as BaseDataset, CLDFSpec
from pycldf.sources import Source, Reference
from csvw.metadata import URITemplate

from mediautil import contribution_media, MediaTable, Contributors, LanguageMetadata, TableOfContents, LanguageContributions

ObjectsType = dict[str, list[dict[str, typing.Any]]]
PkMapType = dict[str, dict[str, str]]
LEXIFIER_DESC = """\
To help the reader’s orientation, we have classified our languages into English-based, Dutch-based, 
Portuguese-based, and so on. This classification is not entirely uncontroversial. On the one hand, 
contact languages are characterized by strong influence from multiple languages, so saying, for 
instance, that Haitian Creole is French-based is problematic, as it glosses over the very important 
contribution of the African languages, especially to the grammar of the language. For this reason, 
many authors have used expressions like “French-lexified”, “Dutch-lexified” for such languages, 
which only refer to the role of the European languages as primary lexicon-providers. We agree that 
such terms are more precise, but they are also more cumbersome, so we have mostly used the older 
(and still much more widespread) manner of talking about groups of creoles and pidgins. We think 
that it is sufficiently well-known that “English-based” (etc.) is not meant to imply anything other 
than that the bulk of the language’s lexicon is derived from English.

On the other hand, the notion of being based on a language is problematic in the case of languages 
with several lexifiers, especially Gurindji Kriol and Michif. These are shown as having two 
lexifiers (or lexifier "other"). There are also a few other cases where it is not fully clear what
the primary lexifier is. Saramaccan’s vocabulary has a very large Portuguese component, but for 
simplicity we classify it as English-based here. Papiamentu is often thought to be originally 
(Afro-)Portuguese-based, but as it has long been influenced much more by Spanish, we classify it 
as Spanish-based."""
NON_DEFAULT_LECT = """\
Sometimes the languages or varieties that the APiCS language experts described were not internally 
homogeneous, but different subvarieties (or lects) had different value choices for some feature. 
Such non-default lects are marked with a non-empty "Default_Lect_ID" column, relating the (sub)lect
with a default lect. Thus the default lect that was primarily described by the contributors need 
not be representative for the entire language."""
CONFIDENCE_FIX = {
    'very certain': 'Very certain',
    'unspecified': 'Unspecified',
}


class Dataset(BaseDataset):
    dir = pathlib.Path(__file__).parent
    id = "apics"

    def cldf_specs(self):  # A dataset must declare all CLDF sets it creates.
        return CLDFSpec(module='StructureDataset', dir=self.cldf_dir)

    def cmd_download(self, args):
        pass

    @functools.cached_property
    def cdstar(self):
        res = {}
        for oid, md in load(self.raw_dir / 'cdstar.json').items():
            for bs in md['bitstreams']:
                assert bs['bitstreamid'] not in res
                #
                # FIXME: make sure we have this in s3!
                #
                res[bs['bitstreamid']] = (
                    'https://cdstar.eva.mpg.de/bitstreams/{}/{}'.format(oid, bs['bitstreamid']),
                    bs['checksum'])
        return res

    def get_file(self, obj, suffix=None):
        bsid = obj['jsondata']['original']
        url, checksum = self.cdstar[bsid]
        p = self.raw_dir / 'media' / bsid
        if suffix:
            assert p.suffix == suffix
        if not p.exists():
            urllib.request.urlretrieve(url, str(p))
        assert md5(p) == checksum
        return p, checksum

    def write_file(self, d, fname, content):
        dest = self.cldf_dir.joinpath(d, fname)
        dest.write_text(content, encoding='utf8')
        return dest

    def cmd_readme(self, args):
        res = super().cmd_readme(args)
        return res + """

### Overview

This dataset bundles the data of the *Atlas of Pidgin and Creole Language Structures* (APiCS),
originally published as a set of four books by Oxford University Press. It contains 
- the expert-coded grammatical and lexical features described in the printed Atlas [as CLDF StructureDataset](cldf/)
- the feature descriptions [as HTML pages and feature maps in Gall-Peters projection as PDF](cldf/Atlas)
- the surveys [as HTML pages](cldf/Survey)
- accompanying media such as the glossed texts provided with each survey or [audio files of spoken examples](cldf/Examples)

To browse the HTML pages contained herein, download the dataset and open `cldf/index.html` in
your browser.


### Coverage

APiCS covers 76 pidgin and creole languages from around the world.

![map](map.svg)

"""

    def cmd_makecldf(self, args):
        media = MediaTable.from_cdstar(
            args.writer.objects, self.cldf_dir, load(self.raw_dir / 'cdstar.json'))
        self.create_schema(args.writer.cldf, media)
        for subdirs in ['Atlas', 'Survey', 'Examples']:
            d = self.cldf_dir / subdirs
            d.mkdir(exist_ok=True)

        pk2id: PkMapType = collections.defaultdict(dict)
        args.writer.cldf.add_sources(*list(self.itersources(pk2id)))
        self.read('source', pkmap=pk2id)

        contributors = Contributors.from_contrib_rows(
            self.read('contributor', pkmap=pk2id, key=lambda r: r['id']).values(),
            self.contributor_ids('contributioncontributor', pk2id, 'contribution_pk'),
            self.contributor_ids('surveycontributor', pk2id, 'survey_pk'),
            self.contributor_ids('featureauthor', pk2id, 'feature_pk'),
        )
        args.writer.objects['contributors.csv'] = contributors.contributors

        index = TableOfContents()
        self._add_languages(args.writer.objects, pk2id, media, contributors, index)
        args.writer.objects['LanguageTable'].sort(key=lambda d: d['ID'])

        for row in self.read(
                'parameter',
                extended='feature',
                pkmap=pk2id,
                key=lambda d: int(d['id'])).values():
            self._add_feature(row, args.writer.objects, media, contributors, index)

        index.write(self.cldf_dir / 'index.html')
        example_by_value = self._add_examples(args.writer.objects, pk2id, media)
        self._add_values(args.writer.objects, pk2id, example_by_value)

    def _add_values(
            self,
            objects: ObjectsType,
            pk2id: PkMapType,
            example_by_value,
    ):
        for row in self.read(
                'domainelement',
                pkmap=pk2id,
                key=lambda d: (int(d['id'].split('-')[0]), int(d['number']))).values():
            objects['CodeTable'].append({
                'ID': row['id'],
                'Parameter_ID': pk2id['parameter'][row['parameter_pk']],
                'Name': row['name'],
                'Description': row['description'],
                'Number': int(row['number']),
                'icon': row['jsondata']['icon'],
                'color': row['jsondata']['color'],
                'abbr': row['abbr'],
            })

        refs = dict(self._get_refs('valueset', pk2id))
        vsdict = self.read('valueset', pkmap=pk2id)

        for row in self.read('value').values():
            vs = vsdict[row['valueset_pk']]
            objects['ValueTable'].append({
                'ID': row['id'],
                'Language_ID': pk2id['language'][vs['language_pk']],
                'Parameter_ID': pk2id['parameter'][vs['parameter_pk']],
                'Value': pk2id['domainelement'][row['domainelement_pk']].split('-')[1],
                'Code_ID': pk2id['domainelement'][row['domainelement_pk']],
                'Comment': vs['description'],
                'Source': refs.get(vs['pk'], []),
                'Example_ID': example_by_value.get(row['pk'], []),
                'Frequency': float(row['frequency']) if row['frequency'] else None,
                'Confidence': CONFIDENCE_FIX.get(row['confidence'], row['confidence']),
                'Metadata': json.dumps(collections.OrderedDict(
                    sorted(vs['jsondata'].items(), key=lambda i: i[0]))),
                'source_comment': vs['source'],
            })

        objects['ValueTable'].sort(key=lambda d: (d['Language_ID'], d['Parameter_ID']))

    def _add_examples(self, objects: ObjectsType, pk2id: PkMapType, media: MediaTable):
        exrefs = dict(self._get_refs('sentence', pk2id))
        igts = {}
        for ex in self.read('sentence', pkmap=pk2id).values():
            audio, a, g = None, [], []
            files = ex.get('files', [])
            if files:
                assert len(files) == 1, ex
                src, audio = self.get_file(files[0], suffix='.mp3')
                media.add(
                    src,
                    'Audio of the spoken object language text of examples',
                    dest='Examples',
                    lids=[pk2id['language'][ex['language_pk']]],
                    md5sum=audio)

            if ex['analyzed']:
                a = ex['analyzed'].split()
            if ex['gloss']:
                g = ex['gloss'].split()
            if len(a) != len(g):
                a, g = [ex['analyzed']], [ex['gloss']]
            igts[ex['pk']] = ex['id']
            objects['ExampleTable'].append({
                'ID': ex['id'],
                'Language_ID': pk2id['language'][ex['language_pk']],
                'Primary_Text': ex['name'],
                'Translated_Text': ex['description'],
                'Analyzed_Word': a,
                'Gloss': g,
                'Source': exrefs.get(ex['pk'], []),
                'Type': ex['type'],
                'Audio': audio,
                'Comment': ex['comment'],
                'source_comment': ex['source'],
                'original_script': ex['original_script'],
                'markup_comment': ex['markup_comment'],
                'markup_text': ex['markup_text'],
                'markup_analyzed': ex['markup_analyzed'],
                'markup_gloss': ex['markup_gloss'],
                'sort': ex['jsondata'].get('sort'),
                'alt_translation': ex['jsondata'].get('alt_translation'),
            })

        for row in self.read('glossabbreviation').values():
            objects['glossabbreviations.csv'].append(
                dict(ID=row['id'], Name=row['name']))
        example_by_value = {
            vpk: [r['sentence_pk'] for r in rows]
            for vpk, rows in itertools.groupby(
                self.read('valuesentence', key=lambda d: d['value_pk']).values(),
                lambda d: d['value_pk'])}
        return {
            vpk: sorted(igts[epk] for epk in epks)
            for vpk, epks in example_by_value.items()}

    def _add_languages(
            self,
            objects: ObjectsType,
            pk2id: PkMapType,
            media: MediaTable,
            contributors: Contributors,
            index: TableOfContents,
    ):
        lmeta = LanguageMetadata.from_csv(self.read, pk2id)
        contribs = LanguageContributions.from_surveys_and_contribs(
            self.read('survey'),
            self.read('contribution', extended='apicscontribution'))

        # Loop over languages ordered such that "proper" languages are hit first and ordered by id.
        for row in self.read(
                'language',
                extended='lect',
                pkmap=pk2id,
                key=lambda l: (bool(l['language_pk']), int(l['id'])),
        ).values():
            self._add_language(
                row,
                lmeta,
                contribs.contributions(row['id']),
                objects,
                contributors,
                media,
                index,
            )

    def _add_language(
            self,
            row,
            meta: LanguageMetadata,
            contribs,
            objects,
            contributors,
            media: MediaTable,
            index: TableOfContents,
    ):
        meta.pk2id[row['pk']] = row['id']
        assert contribs.survey or (int(row['id']) == 21 or int(row['id']) > 100)
        objects['LanguageTable'].append(meta.update(
            {
                'ID': row['id'],
                'Name': row['name'],
                'Description': contribs.structdataset[
                    'markup_description'] if contribs.structdataset else '',
                'Latitude': row['latitude'],
                'Longitude': row['longitude'],
                'Region': row['region'],
                'Default_Lect_ID': meta.pk2id.get(row['language_pk']),
                'Lexifier': row['lexifier'],
            },
            row['pk']))
        if meta.pk2id.get(row['language_pk']):
            return
        # Create the two related contributions: StructureDataset and SurveyChapter
        objects['ContributionTable'].append(contribs.structuredataset_as_contribution(
            contributors.contrib_spec(contributors.cc_ids[contribs.structdataset['pk']]),
            contributors.editor_names,
            row['name']))
        survey_html = self.raw_dir.joinpath('Surveys', f"{row['id']}.html")
        if survey_html.exists():
            assert contribs.survey
            index.add_survey(contribs.survey, survey_html.name)

            objects['ContributionTable'].append(contribs.survey_as_contribution(
                contributors.contrib_spec(contributors.sc_ids[row['pk']]),
                contributors.editor_names))
            gt_audio, gt_pdf = contribs.add_glossed_text(media, self.get_file, row['name'])
            extra = None
            if gt_audio or gt_pdf:
                extra = [HTML.h2('Glossed text')]
                if gt_audio:
                    extra.append(HTML.p(HTML.audio(controls='controls', src=gt_audio)))
                if gt_pdf:
                    extra.append(HTML.p(HTML.a('[PDF]', href=gt_pdf)))
                extra = HTML.div(*extra)

            html, maps = contribution_media(self.etc_dir, self.raw_dir / 'Surveys', row['id'], extra_section=extra)
            sid = f"s-{row['id']}"
            media.add(
                self.write_file('Survey', survey_html.name, html),
                contribs.survey['name'],
                cid=sid, lids=contribs.survey_lids())
            for src in maps:
                media.add(
                    src,
                    f"Map or figure accompanying language survey {contribs.survey['name']}",
                    dest='Survey', cid=sid, lids=contribs.survey_lids())

    def _add_feature(
            self,
            row: dict[str, str],
            objects: ObjectsType,
            media: MediaTable,
            contributors,
            index: TableOfContents):
        """
        A feature in APiCS is considered a citeable contribution. Thus, adding a feature means
        adding
        - a Parameter
        - a Contributio
        - possibly media files: a map in Gall-Peters projection and/or the chapter text.
        """
        objects['ParameterTable'].append({
            'ID': row['id'],
            'Name': row['name'],
            'Description': row['markup_description'] if row['id'] != '0' else LEXIFIER_DESC,
            'Type': row['feature_type'],
            'PHOIBLE_Segment_ID': row['jsondata'].get('phoible', {}).get('id'),
            'PHOIBLE_Segment_Name': row['jsondata'].get('phoible', {}).get('segment'),
            #multivalued,wals_id,wals_representation,representation,area
            'Multivalued': row['multivalued'] == 't',
            'WALS_ID': (row['wals_id'] + 'A') if row['wals_id'] else '',
            'WALS_Representation': int(row['wals_representation']) if row['wals_representation'] else None,
            'Area': row['area'],
            'metadata': json.dumps(collections.OrderedDict(
                sorted(row['jsondata'].items(), key=lambda i: i[0]))),
        })
        obj = contributors.contrib_spec(contributors.fc_ids.get(row['pk'], []))
        obj.update({
            'ID': f"a-{row['id']}",
            'type': 'AtlasChapter',
            'Name': row['name'],
            'Parameter_ID': row['id'],
        })
        obj['Citation'] = \
            "{Contributor} and the APiCS Consortium. 2013. {Name}. In: {eds} " \
            "(eds.) The Atlas of Pidgin and Creole Language Structures. " \
            "Oxford: Oxford University Press.".format(eds=contributors.editor_names, **obj)
        objects['ContributionTable'].append(obj)
        files = row.get('files', [])
        if files:
            assert len(files) == 1, row
            media.add(
                self.get_file(files[0], suffix='.pdf')[0],
                'Map of the values for feature {} in Gall-Peters projection'.format(row['id']),
                dest='Atlas',
                cid=obj['ID'])

        chapter_name = f"{row['id']}.html"
        if self.raw_dir.joinpath('Atlas', chapter_name).exists():
            index.add_atlas_chapter(row, chapter_name)
            html, maps = contribution_media(
                self.etc_dir, self.raw_dir / 'Atlas', row['id'],
                title=row['name'], author=obj['Contributor'])
            assert not maps
            media.add(self.write_file('Atlas', chapter_name, html), row['name'], cid=obj['ID'])

    def _get_refs(self, referent: typing.Literal['valueset', 'sentence'], pk2id: PkMapType):
        def _reference_from_row(row: dict[str, typing.Any]) -> Reference:
            return Reference(
                source=pk2id['source'][row['source_pk']],
                desc=row['description'].replace('[', '(').replace(']', ')').replace(';', '.').strip()
                if row['description'] else None)

        for rpk, rows in itertools.groupby(
            sorted(
                self.raw_dir.read_csv(f'{referent}reference.csv', dicts=True),
                key=operator.itemgetter(f'{referent}_pk')),
            operator.itemgetter(f'{referent}_pk')
        ):
            yield rpk, [str(_reference_from_row(row)) for row in rows if row['source_pk']]

    def create_schema(self, cldf, media: MediaTable):
        cldf.add_component(
            'LanguageTable',
            {
                'name': 'Description',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#description',
                'dc:format': 'text/html',
            },
            {
                'name': 'Source',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source',
                'separator': ';',
            },
            'Ethnologue_Name',
            {
                'name': 'Metadata',
                'dc:format': 'text/json',
            },
            'Region',
            {
                'name': 'Default_Lect_ID',
                'dc:description': NON_DEFAULT_LECT,
            },
            {
                'name': 'Lexifier',
                'dc:description': LEXIFIER_DESC,
            },
        )
        cldf['LanguageTable', 'id'].valueUrl = URITemplate(
            'https://apics-online.info/contributions/{ID}')
        cldf.add_component(
            'ParameterTable',
            {
                'name': 'Type',
                'dc:description': "Primary or structural feature, segment or sociolinguistic feature",
            },
            {
                'name': 'PHOIBLE_Segment_ID',
                'valueUrl': 'https://phoible.org/parameters/{PHOIBLE_Segment_ID}',
            },
            'PHOIBLE_Segment_Name',
            {'name': 'Multivalued', 'datatype': 'boolean'},
            {
                'name': 'WALS_ID',
                'dc:description': 'ID of the corresponding WALS feature',
            },
            {'name': 'WALS_Representation', 'datatype': 'integer'},
            'Area',
            {'name': 'metadata', 'dc:format': 'application/json'},
        )
        cldf['ParameterTable', 'id'].valueUrl = URITemplate(
            'https://apics-online.info/parameters/{ID}')
        t = cldf.add_table(
            'contributors.csv',
            {
                'name': 'ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id',
            },
            {
                'name': 'Name',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#name',
            },
            'Address',
            'URL',
            {
                'name': 'editor_ord',
                'datatype': 'integer',
            }
        )
        t.common_props['dc:conformsTo'] = None
        cldf.add_component(
            'ContributionTable',
            'type',  # survey, structure-dataset, feature, other
            {
                'name': 'Contributor_IDs',
                'separator': ' ',
            },
            {
                'name': 'Parameter_ID',
                'propertyUrl': "http://cldf.clld.org/v1.0/terms.rdf#parameterReference",
                'dc:description':
                    "APiCS Atlas chapters describe features. Thus, for contributions of type "
                    "AtlasChapter, this column links to the relevant parameter."
            },
            {
                'name': 'Language_IDs',
                'propertyUrl': "http://cldf.clld.org/v1.0/terms.rdf#languageReference",
                'separator': ' ',
                'dc:description':
                    "APiCS structure datasets and survey chapters describe languages. Thus, "
                    "for contributions of type StructureDataset or SurveyChapter, this column "
                    "links to the relevant language(s).",
            }
        )
        cldf.add_foreign_key('ContributionTable', 'Contributor_IDs', 'contributors.csv', 'ID')
        cldf.add_table(
            'glossabbreviations.csv',
            {
                'name': 'ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id',
            },
            {
                'name': 'Name',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#name',
            })
        cldf.add_component(
            'CodeTable',
            {'name': 'Number', 'datatype': 'integer'},
            'icon',
            'color',
            'abbr',
        )
        media.schema(cldf)
        cldf.add_component(
            'ExampleTable',
            {
                'name': 'Source',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source',
                'separator': ';',
            },
            {
                'name': 'Audio',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#mediaReference',
            },
            {'name': 'Type', 'propertyUrl': 'dc:type'},
            {
                'name': 'markup_text',
                'dc:format': 'text/html',
            },
            {
                'name': 'markup_analyzed',
                'dc:format': 'text/html',
            },
            {
                'name': 'markup_gloss',
                'dc:format': 'text/html',
            },
            {
                'name': 'markup_comment',
                'dc:format': 'text/html',
            },
            'source_comment',
            'original_script',
            'sort',
            'alt_translation',
        )
        cldf.add_columns(
            'ValueTable',
            {
                'name': 'Example_ID',
                'separator': ' ',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#exampleReference',
            },
            {
                'name': 'Frequency',
                "datatype": 'number',
            },
            'Confidence',
            {
                'name': 'Metadata',
                'dc:format': 'text/json',
            },
            'source_comment',
        )

    def read(self, core, extended=False, pkmap=None, key=None):
        if not key:
            key = lambda d: int(d['pk'])
        res = collections.OrderedDict()
        for row in self.raw_dir.read_csv('{0}.csv'.format(core), dicts=True):
            row['jsondata'] = json.loads(row.get('jsondata') or '{}')
            res[row['pk']] = row
            if pkmap is not None:
                pkmap[core][row['pk']] = row['id']
        if extended:
            for row in self.raw_dir.read_csv('{0}.csv'.format(extended), dicts=True):
                res[row['pk']].update(row)
        res = collections.OrderedDict(sorted(res.items(), key=lambda item: key(item[1])))
        files = self.raw_dir / '{}_files.csv'.format(core)
        if files.exists():
            for opk, rows in itertools.groupby(
                    sorted(self.raw_dir.read_csv(files.name, dicts=True), key=lambda d: d['object_pk']),
                    lambda d: d['object_pk'],
            ):
                res[opk]['files'] = []
                for row in rows:
                    row['jsondata'] = json.loads(row.get('jsondata') or '{}')
                    res[opk]['files'].append(row)
        return res

    def itersources(self, pkmap):
        for row in self.raw_dir.read_csv('source.csv', dicts=True):
            jsondata = json.loads(row.pop('jsondata', '{}') or '{}')
            pkmap['source'][row.pop('pk')] = row['id']
            row['title'] = row.pop('description')
            row['key'] = row.pop('name')
            if (not row['url']) and jsondata.get('gbs', {}).get('id'):
                row['url'] = 'https://books.google.de/books?id=' + jsondata['gbs']['id']
            yield Source(row.pop('bibtex_type'), row.pop('id'), **row)

    def contributor_ids(self, name, pk2id, fkcol):
        return {
            fid: [pk2id['contributor'][r['contributor_pk']] for r in rows]
            for fid, rows in itertools.groupby(
                self.read(
                    name,
                    key=lambda d: (d[fkcol], d.get('primary') == 'f', int(d['ord']))
                ).values(),
                lambda r: r[fkcol])
        }
