import json
import pathlib
import itertools
import collections

from clldutils.misc import lazyproperty
from cldfbench import Dataset as BaseDataset, CLDFSpec
from pycldf.sources import Source, Reference
from csvw.metadata import URITemplate

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

    def cmd_makecldf(self, args):
        self.create_schema(args.writer.cldf)
        pk2id = collections.defaultdict(dict)
        checksums = set()
        args.writer.cldf.add_sources(*list(self.itersources(pk2id)))
        self.read('source', pkmap=pk2id)

        refs = []
        for row in self.raw_dir.read_csv('valuesetreference.csv', dicts=True):
            if row['source_pk']:
                refs.append((row['valueset_pk'], pk2id['source'][row['source_pk']], row['description']))
        exrefs = []
        for row in self.raw_dir.read_csv('sentencereference.csv', dicts=True):
            if row['source_pk']:
                exrefs.append((row['sentence_pk'], pk2id['source'][row['source_pk']], row['description']))

        editors = {
            name: ord for ord, name in enumerate([
                'Susanne Maria Michaelis',
                'Philippe Maurer',
                'Martin Haspelmath',
                'Magnus Huber',
            ], start=1)}

        for row in self.read('contributor', pkmap=pk2id, key=lambda r: r['id']).values():
            args.writer.objects['contributors.csv'].append({
                'ID': row['id'],
                'Name': row['name'],
                'Address': row['address'],
                'URL': row['url'],
                'editor_ord': editors.get(row['name']),
            })

        cc = self.contributor_ids('contributioncontributor', pk2id, 'contribution_pk')
        scc = self.contributor_ids('surveycontributor', pk2id, 'survey_pk')

        # We put contribution data into the language table!
        contribs = self.read('contribution', extended='apicscontribution')
        gts = self.add_files(args.writer, contribs.values(), checksums)
        contribs = {c['id']: c for c in contribs.values()}
        surveys = {c['id']: c for c in self.read('survey').values()}
        surveys['51'] = surveys['50']
        identifier = self.read('identifier')
        lang2id = collections.defaultdict(lambda: collections.defaultdict(list))
        for row in self.read('languageidentifier').values():
            id_ = identifier[row['identifier_pk']]
            lang2id[row['language_pk']][id_['type']].append((id_['name'], id_['description']))
        lrefs = {
            lpk: set(pk2id['source'][r['source_pk']] for r in rows)
            for lpk, rows in itertools.groupby(
                self.read('languagesource', key=lambda d: d['language_pk']).values(),
                lambda d: d['language_pk'])}
        for row in self.read('contributionreference').values():
            lrefs[row['contribution_pk']].add(pk2id['source'][row['source_pk']])

        ldata = {}
        for lpk, rows in itertools.groupby(
            self.read('language_data', key=lambda d: (d['object_pk'], int(d['ord']))).values(),
            lambda d: d['object_pk'],
        ):
            ldata[lpk] = collections.OrderedDict([(d['key'], d['value']) for d in rows])

        lmap = {}
        for row in self.read(
            'language',
            extended='lect',
            pkmap=pk2id,
            key=lambda l: (bool(l['language_pk']), int(l['id'])),
        ).values():
            lmap[row['pk']] = id = row['id']
            contrib = contribs.get(id)
            survey = surveys.get(row['id'])
            assert survey or (int(id) == 21 or int(id) > 100)
            iso_codes = set(i[0] for i in lang2id[row['pk']].get('iso639-3', []))
            glottocodes = [i[0] for i in lang2id[row['pk']].get('glottolog', [])]
            ethnologue_names = [i[0] for i in lang2id[row['pk']].get('ethnologue', [])]
            lrefs_ = [Reference(r, None) for r in sorted(lrefs.get(row['pk'], []))]
            gt_pdf, gt_audio = None, None
            if contrib:
                lrefs_.append(Reference(pk2id['source'][contrib['survey_reference_pk']], desc='survey'))
                for f in contrib.get('files', []):
                    if f['id'].endswith('pdf'):
                        gt_pdf = gts[(f['jsondata']['objid'], f['jsondata']['original'])]
                    if f['id'].endswith('mp3'):
                        gt_audio = gts[(f['jsondata']['objid'], f['jsondata']['original'])]
            args.writer.objects['LanguageTable'].append({
                'ID': id,
                'Name': row['name'],
                'Description': contrib['markup_description'] if contrib else '',
                'ISO639P3code': list(iso_codes)[0] if len(iso_codes) == 1 else None,
                'Glottocode': glottocodes[0] if len(glottocodes) == 1 else None,
                'Ethnologue_Name': ', '.join(ethnologue_names),
                'Latitude': row['latitude'],
                'Longitude': row['longitude'],
                'Data_Contributor_ID': cc[contrib['pk']] if contrib else [],
                'Survey_Contributor_ID': scc[survey['pk']] if survey else [],
                'Survey_Title': '{}. In "The survey of pidgin and creole languages". {}'.format(
                    survey['name'], survey['description']) if survey else '',
                'Source': [str(r) for r in lrefs_],
                'Glossed_Text_PDF': gt_pdf,
                'Glossed_Text_Audio': gt_audio,
                'Metadata': json.dumps(ldata.get(row['pk'], {})),
                'Region': row['region'],
                'Default_Lect_ID': lmap.get(row['language_pk']),
                'Lexifier': row['lexifier'],
            })
        args.writer.objects['LanguageTable'].sort(key=lambda d: d['ID'])

        fcc = self.contributor_ids('featureauthor', pk2id, 'feature_pk')
        for row in self.read(
                'parameter',
                extended='feature',
                pkmap=pk2id,
                key=lambda d: d['id']).values():
            mgp = None
            maps = self.add_files(args.writer, [row], checksums)
            for f in row.get('files', []):
                if f['id'].endswith('pdf'):
                    mgp = maps[(f['jsondata']['objid'], f['jsondata']['original'])]
            args.writer.objects['ParameterTable'].append({
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
                'Contributor_ID': fcc.get(row['pk'], []),
                'Map_Gall_Peters': mgp,
                'metadata': json.dumps(collections.OrderedDict(
                    sorted(row['jsondata'].items(), key=lambda i: i[0]))),
            })

        for row in self.read(
                'domainelement',
                pkmap=pk2id,
                key=lambda d: (int(d['id'].split('-')[0]), int(d['number']))).values():
            args.writer.objects['CodeTable'].append({
                'ID': row['id'],
                'Parameter_ID': pk2id['parameter'][row['parameter_pk']],
                'Name': row['name'],
                'Description': row['description'],
                'Number': int(row['number']),
                'icon': row['jsondata']['icon'],
                'color': row['jsondata']['color'],
                'abbr': row['abbr'],
            })

        refs = {
            dpid: [
                str(Reference(
                    source=str(r[1]),
                    desc=r[2].replace('[', ')').replace(']', ')').replace(';', '.').strip()
                    if r[2] else None))
                for r in refs_
            ]
            for dpid, refs_ in itertools.groupby(refs, lambda r: r[0])}

        vsdict = self.read('valueset', pkmap=pk2id)
        examples = self.read('sentence', pkmap=pk2id)
        mp3 = self.add_files(args.writer, examples.values(), checksums)
        igts = {}
        exrefs = {
            dpid: [
                str(Reference(
                    source=str(r[1]),
                    desc=r[2].replace('[', ')').replace(']', ')').replace(';', '.').strip()
                    if r[2] else None))
                for r in refs_
            ]
            for dpid, refs_ in itertools.groupby(exrefs, lambda r: r[0])}

        for ex in examples.values():
            audio, a, g = None, [], []
            for f in ex.get('files', []):
                if f['id'].endswith('mp3'):
                    audio = mp3[(f['jsondata']['objid'], f['jsondata']['original'])]
            if ex['analyzed']:
                a = ex['analyzed'].split()
            if ex['gloss']:
                g = ex['gloss'].split()
            if len(a) != len(g):
                a, g = [ex['analyzed']], [ex['gloss']]
            igts[ex['pk']] = ex['id']
            args.writer.objects['ExampleTable'].append({
                'ID': ex['id'],
                'Language_ID': pk2id['language'][ex['language_pk']],
                'Primary_Text': ex['name'],
                'Translated_Text': ex['description'],
                'Analyzed_Word': a,
                'Gloss': g,
                'Source': exrefs.get(ex['pk'], []),
                'Audio': audio,
                'Type': ex['type'],
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
        example_by_value = {
            vpk: [r['sentence_pk'] for r in rows]
            for vpk, rows in itertools.groupby(
                self.read('valuesentence', key=lambda d: d['value_pk']).values(),
                lambda d: d['value_pk'])}

        for row in self.read('value').values():
            vs = vsdict[row['valueset_pk']]
            args.writer.objects['ValueTable'].append({
                'ID': row['id'],
                'Language_ID': pk2id['language'][vs['language_pk']],
                'Parameter_ID': pk2id['parameter'][vs['parameter_pk']],
                'Value': pk2id['domainelement'][row['domainelement_pk']].split('-')[1],
                'Code_ID': pk2id['domainelement'][row['domainelement_pk']],
                'Comment': vs['description'],
                'Source': refs.get(vs['pk'], []),
                'Example_ID': sorted(igts[epk] for epk in example_by_value.get(row['pk'], []) if epk in igts),
                'Frequency': float(row['frequency']) if row['frequency'] else None,
                'Confidence': CONFIDENCE_FIX.get(row['confidence'], row['confidence']),
                'Metadata': json.dumps(collections.OrderedDict(
                    sorted(vs['jsondata'].items(), key=lambda i: i[0]))),
                'source_comment': vs['source'],
            })

        args.writer.objects['ValueTable'].sort(
            key=lambda d: (d['Language_ID'], d['Parameter_ID']))

        for row in self.read('glossabbreviation').values():
            args.writer.objects['glossabbreviations.csv'].append(
                dict(ID=row['id'], Name=row['name']))

    def create_schema(self, cldf):
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
        cldf.add_table(
            'media.csv',
            {
                'name': 'ID',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#id',
                'valueUrl': 'https://cdstar.shh.mpg.de/bitstreams/{Name}',
            },
            {
                'name': 'Name',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#name',
            },
            {
                'name': 'Description',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#description',
            },
            'mimetype',
            {'name': 'size', 'datatype': 'integer'},
        )

        cldf.add_component(
            'ParameterTable',
            {
                'name': 'Contributor_ID',
                'separator': ' ',
                'dc:description': 'Authors of the Atlas chapter describing the feature',
            },
            'Chapter',  # valueUrl: https://apics-online.info/parameters/1.chapter.html
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
            'Map_Gall_Peters',
            {'name': 'metadata', 'dc:format': 'application/json'},
        )
        cldf['ParameterTable', 'id'].valueUrl = URITemplate(
            'https://apics-online.info/parameters/{id}')
        cldf.add_component(
            'CodeTable',
            {'name': 'Number', 'datatype': 'integer'},
            'icon',
            'color',
            'abbr',
        )
        cldf.add_component(
            'LanguageTable',
            {
                'name': 'Description',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#description',
                'dc:format': 'text/html',
            },
            {
                'name': 'Data_Contributor_ID',
                'separator': ' ',
                'dc:description': 'Authors contributing the language structure dataset',
            },
            {
                'name': 'Survey_Contributor_ID',
                'separator': ' ',
                'dc:description': 'Authors of the language survey',
            },
            'Survey_Title',
            {
                'name': 'Source',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source',
                'separator': ';',
            },
            'Ethnologue_Name',
            'Glossed_Text_PDF',
            'Glossed_Text_Audio',
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
            'https://apics-online.info/contributions/{id}')
        cldf.add_component(
            'ExampleTable',
            {
                'name': 'Source',
                'propertyUrl': 'http://cldf.clld.org/v1.0/terms.rdf#source',
                'separator': ';',
            },
            'Audio',
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
        cldf.add_foreign_key('ParameterTable', 'Contributor_ID', 'contributors.csv', 'ID')
        cldf.add_foreign_key('ParameterTable', 'Map_Gall_Peters', 'media.csv', 'ID')
        cldf.add_foreign_key('LanguageTable', 'Glossed_Text_PDF', 'media.csv', 'ID')
        cldf.add_foreign_key('LanguageTable', 'Glossed_Text_Audio', 'media.csv', 'ID')
        cldf.add_foreign_key('ExampleTable', 'Audio', 'media.csv', 'ID')

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

    def add_files(self, writer, objs, checksums):
        res = {}
        for c in objs:
            for f in c.get('files', []):
                md = f['jsondata']
                id_ = self.cdstar[md['objid'], md['original']][0]
                if id_ not in checksums:
                    checksums.add(id_)
                    writer.objects['media.csv'].append({
                        # maybe base64 encode? or use md5 hash from catalog?
                        'ID': id_,
                        'Name': '{}/{}'.format(md['objid'], md['original']),
                        'Description': self.cdstar[md['objid'], md['original']][1],
                        'mimetype': md['mimetype'],
                        'size': md['size'],
                })
                res[(md['objid'], md['original'])] = id_
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

    @lazyproperty
    def cdstar(self):
        cdstar = {}
        for eid, md in self.raw_dir.read_json('cdstar.json').items():
            for bs in md['bitstreams']:
                cdstar[eid, bs['bitstreamid']] = (bs['checksum'], md['metadata'].get('description'))
        return cdstar

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
