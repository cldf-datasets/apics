<a name="ds-structuredatasetmetadatajson"> </a>

# StructureDataset Atlas of Pidgin and Creole Language Structures Online

**CLDF Metadata**: [StructureDataset-metadata.json](./StructureDataset-metadata.json)

**Sources**: [sources.bib](./sources.bib)

property | value
 --- | ---
[dc:bibliographicCitation](http://purl.org/dc/terms/bibliographicCitation) | Michaelis, Susanne Maria & Maurer, Philippe & Haspelmath, Martin & Huber, Magnus (eds.) 2013. Atlas of Pidgin and Creole Language Structures Online. Leipzig: Max Planck Institute for Evolutionary Anthropology.
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF StructureDataset](http://cldf.clld.org/v1.0/terms.rdf#StructureDataset)
[dc:identifier](http://purl.org/dc/terms/identifier) | https://apics-online.info/
[dc:license](http://purl.org/dc/terms/license) | https://creativecommons.org/licenses/by/4.0/
[dcat:accessURL](http://www.w3.org/ns/dcat#accessURL) | https://github.com/cldf-datasets/apics
[prov:wasDerivedFrom](http://www.w3.org/ns/prov#wasDerivedFrom) | <ol><li><a href="https://github.com/cldf-datasets/apics/tree/f687a83">cldf-datasets/apics  v2013-24-gf687a83</a></li><li><a href="https://github.com/glottolog/glottolog/tree/v5.3">Glottolog  v5.3</a></li></ol>
[prov:wasGeneratedBy](http://www.w3.org/ns/prov#wasGeneratedBy) | <ol><li><strong>python</strong>: 3.12.3</li><li><strong>python-packages</strong>: <a href="./requirements.txt">requirements.txt</a></li></ol>
[rdf:ID](http://www.w3.org/1999/02/22-rdf-syntax-ns#ID) | apics
[rdf:type](http://www.w3.org/1999/02/22-rdf-syntax-ns#type) | http://www.w3.org/ns/dcat#Distribution


## <a name="table-valuescsv"></a>Table [values.csv](./values.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ValueTable](http://cldf.clld.org/v1.0/terms.rdf#ValueTable)
[dc:extent](http://purl.org/dc/terms/extent) | 20624


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)
[Parameter_ID](http://cldf.clld.org/v1.0/terms.rdf#parameterReference) | `string` | References [parameters.csv::ID](#table-parameterscsv)
[Value](http://cldf.clld.org/v1.0/terms.rdf#value) | `string` | 
[Code_ID](http://cldf.clld.org/v1.0/terms.rdf#codeReference) | `string` | References [codes.csv::ID](#table-codescsv)
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
[Example_ID](http://cldf.clld.org/v1.0/terms.rdf#exampleReference) | list of `string` (separated by ` `) | References [examples.csv::ID](#table-examplescsv)
`Frequency` | `number` | 
`Confidence` | `string` | 
`Metadata` | `string` | 
`source_comment` | `string` | 

## <a name="table-languagescsv"></a>Table [languages.csv](./languages.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF LanguageTable](http://cldf.clld.org/v1.0/terms.rdf#LanguageTable)
[dc:extent](http://purl.org/dc/terms/extent) | 104


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Macroarea](http://cldf.clld.org/v1.0/terms.rdf#macroarea) | `string` | 
[Latitude](http://cldf.clld.org/v1.0/terms.rdf#latitude) | `decimal`<br>&ge; -90<br>&le; 90 | 
[Longitude](http://cldf.clld.org/v1.0/terms.rdf#longitude) | `decimal`<br>&ge; -180<br>&le; 180 | 
[Glottocode](http://cldf.clld.org/v1.0/terms.rdf#glottocode) | `string`<br>Regex: `[a-z0-9]{4}[1-9][0-9]{3}` | 
[ISO639P3code](http://cldf.clld.org/v1.0/terms.rdf#iso639P3code) | `string`<br>Regex: `[a-z]{3}` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
`Ethnologue_Name` | `string` | 
`Metadata` | `string` | 
`Region` | `string` | 
`Default_Lect_ID` | `string` | Sometimes the languages or varieties that the APiCS language experts described were not internally  homogeneous, but different subvarieties (or lects) had different value choices for some feature.  Such non-default lects are marked with a non-empty "Default_Lect_ID" column, relating the (sub)lect with a default lect. Thus the default lect that was primarily described by the contributors need  not be representative for the entire language.
`Lexifier` | `string` | To help the reader’s orientation, we have classified our languages into English-based, Dutch-based,  Portuguese-based, and so on. This classification is not entirely uncontroversial. On the one hand,  contact languages are characterized by strong influence from multiple languages, so saying, for  instance, that Haitian Creole is French-based is problematic, as it glosses over the very important  contribution of the African languages, especially to the grammar of the language. For this reason,  many authors have used expressions like “French-lexified”, “Dutch-lexified” for such languages,  which only refer to the role of the European languages as primary lexicon-providers. We agree that  such terms are more precise, but they are also more cumbersome, so we have mostly used the older  (and still much more widespread) manner of talking about groups of creoles and pidgins. We think  that it is sufficiently well-known that “English-based” (etc.) is not meant to imply anything other  than that the bulk of the language’s lexicon is derived from English.  On the other hand, the notion of being based on a language is problematic in the case of languages  with several lexifiers, especially Gurindji Kriol and Michif. These are shown as having two  lexifiers (or lexifier "other"). There are also a few other cases where it is not fully clear what the primary lexifier is. Saramaccan’s vocabulary has a very large Portuguese component, but for  simplicity we classify it as English-based here. Papiamentu is often thought to be originally  (Afro-)Portuguese-based, but as it has long been influenced much more by Spanish, we classify it  as Spanish-based.

## <a name="table-parameterscsv"></a>Table [parameters.csv](./parameters.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ParameterTable](http://cldf.clld.org/v1.0/terms.rdf#ParameterTable)
[dc:extent](http://purl.org/dc/terms/extent) | 336


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[ColumnSpec](http://cldf.clld.org/v1.0/terms.rdf#columnSpec) | `json` | 
`Type` | `string` | Primary or structural feature, segment or sociolinguistic feature
`PHOIBLE_Segment_ID` | `string` | 
`PHOIBLE_Segment_Name` | `string` | 
`Multivalued` | `boolean` | 
`WALS_ID` | `string` | ID of the corresponding WALS feature
`WALS_Representation` | `integer` | 
`Area` | `string` | 
`metadata` | `string` | 

## <a name="table-contributorscsv"></a>Table [contributors.csv](./contributors.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 90


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
`Address` | `string` | 
`URL` | `string` | 
`editor_ord` | `integer` | 

## <a name="table-contributionscsv"></a>Table [contributions.csv](./contributions.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ContributionTable](http://cldf.clld.org/v1.0/terms.rdf#ContributionTable)
[dc:extent](http://purl.org/dc/terms/extent) | 486


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Contributor](http://cldf.clld.org/v1.0/terms.rdf#contributor) | `string` | 
[Citation](http://cldf.clld.org/v1.0/terms.rdf#citation) | `string` | 
`type` | `string` | 
`Contributor_IDs` | list of `string` (separated by ` `) | References [contributors.csv::ID](#table-contributorscsv)
[Parameter_ID](http://cldf.clld.org/v1.0/terms.rdf#parameterReference) | `string` | APiCS Atlas chapters describe features. Thus, for contributions of type AtlasChapter, this column links to the relevant parameter.<br>References [parameters.csv::ID](#table-parameterscsv)
[Language_IDs](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | list of `string` (separated by ` `) | APiCS structure datasets and survey chapters describe languages. Thus, for contributions of type StructureDataset or SurveyChapter, this column links to the relevant language(s).<br>References [languages.csv::ID](#table-languagescsv)

## <a name="table-glossabbreviationscsv"></a>Table [glossabbreviations.csv](./glossabbreviations.csv)

property | value
 --- | ---
[dc:extent](http://purl.org/dc/terms/extent) | 267


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string` | Primary key
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 

## <a name="table-codescsv"></a>Table [codes.csv](./codes.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF CodeTable](http://cldf.clld.org/v1.0/terms.rdf#CodeTable)
[dc:extent](http://purl.org/dc/terms/extent) | 1404


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Parameter_ID](http://cldf.clld.org/v1.0/terms.rdf#parameterReference) | `string` | The parameter or variable the code belongs to.<br>References [parameters.csv::ID](#table-parameterscsv)
[Name](http://cldf.clld.org/v1.0/terms.rdf#name) | `string` | 
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
`Number` | `integer` | 
`icon` | `string` | 
`color` | `string` | 
`abbr` | `string` | 

## <a name="table-mediacsv"></a>Table [media.csv](./media.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF MediaTable](http://cldf.clld.org/v1.0/terms.rdf#MediaTable)
[dc:extent](http://purl.org/dc/terms/extent) | 750


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Description](http://cldf.clld.org/v1.0/terms.rdf#description) | `string` | 
[Media_Type](http://cldf.clld.org/v1.0/terms.rdf#mediaType) | `string`<br>Regex: `[^/]+/.+` | 
[Download_URL](http://cldf.clld.org/v1.0/terms.rdf#downloadUrl) | `anyURI` | 
[Contribution_ID](http://cldf.clld.org/v1.0/terms.rdf#contributionReference) | `string` | Links to the contribution which contributed the media object.<br>References [contributions.csv::ID](#table-contributionscsv)
[Language_IDs](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | list of `string` (separated by ` `) | Links to languages described by the media object.<br>References [languages.csv::ID](#table-languagescsv)
`size` | `integer` | 
`File_Key` | `string` | 

## <a name="table-examplescsv"></a>Table [examples.csv](./examples.csv)

property | value
 --- | ---
[dc:conformsTo](http://purl.org/dc/terms/conformsTo) | [CLDF ExampleTable](http://cldf.clld.org/v1.0/terms.rdf#ExampleTable)
[dc:extent](http://purl.org/dc/terms/extent) | 18526


### Columns

Name/Property | Datatype | Description
 --- | --- | --- 
[ID](http://cldf.clld.org/v1.0/terms.rdf#id) | `string`<br>Regex: `[a-zA-Z0-9_\-]+` | Primary key
[Language_ID](http://cldf.clld.org/v1.0/terms.rdf#languageReference) | `string` | References [languages.csv::ID](#table-languagescsv)
[Primary_Text](http://cldf.clld.org/v1.0/terms.rdf#primaryText) | `string` | The example text in the source language.
[Analyzed_Word](http://cldf.clld.org/v1.0/terms.rdf#analyzedWord) | list of `string` (separated by `	`) | The sequence of words of the primary text to be aligned with glosses
[Gloss](http://cldf.clld.org/v1.0/terms.rdf#gloss) | list of `string` (separated by `	`) | The sequence of glosses aligned with the words of the primary text
[Translated_Text](http://cldf.clld.org/v1.0/terms.rdf#translatedText) | `string` | The translation of the example text in a meta language
[Meta_Language_ID](http://cldf.clld.org/v1.0/terms.rdf#metaLanguageReference) | `string` | References the language of the translated text<br>References [languages.csv::ID](#table-languagescsv)
[LGR_Conformance](http://cldf.clld.org/v1.0/terms.rdf#lgrConformance) | `string`<br>Valid choices:<br> `WORD_ALIGNED` `MORPHEME_ALIGNED` | The level of conformance of the example with the Leipzig Glossing Rules
[Comment](http://cldf.clld.org/v1.0/terms.rdf#comment) | `string` | 
[Source](http://cldf.clld.org/v1.0/terms.rdf#source) | list of `string` (separated by `;`) | References [sources.bib::BibTeX-key](./sources.bib)
[Audio](http://cldf.clld.org/v1.0/terms.rdf#mediaReference) | `string` | References [media.csv::ID](#table-mediacsv)
[Type](dc:type) | `string` | 
`markup_text` | `string` | 
`markup_analyzed` | `string` | 
`markup_gloss` | `string` | 
`markup_comment` | `string` | 
`source_comment` | `string` | 
`original_script` | `string` | 
`sort` | `string` | 
`alt_translation` | `string` | 
