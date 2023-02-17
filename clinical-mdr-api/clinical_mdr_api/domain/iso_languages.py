"""
https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
ISO 639 is a standardized nomenclature used to classify languages. Each language is
assigned a two-letter (639-1) and three-letter (639-2 and 639-3) lowercase
abbreviation, amended in later versions of the nomenclature.

This list contains all of:
ISO 639-1: two-letter codes, one per language for ISO 639 macrolanguage

And some of:
ISO 639-2/T: three-letter codes, for the same languages as 639-1.
ISO 639-2/B: three-letter codes, mostly the same as 639-2/T, but with some codes
derived from English names rather than native names of languages.
ISO 639-3: three-letter codes, the same as 639-2/T for languages, but with distinct
codes for each variety of an ISO 639 macrolanguage.
"""

_NAMES = "names"
_639_1 = "639-1"
_639_2T = "639-2/T"
_639_2B = "639-2/B"
_639_3 = "639-3"

LANGUAGES = [
    {
        _NAMES: ["Abkhazian"],
        _639_1: "ab",
        _639_2T: "abk",
        _639_2B: "abk",
        _639_3: ["abk"],
    },
    {
        _NAMES: ["Afar"],
        _639_1: "aa",
        _639_2T: "aar",
        _639_2B: "aar",
        _639_3: ["aar"],
    },
    {
        _NAMES: ["Afrikaans"],
        _639_1: "akas",
        _639_2T: "afr",
        _639_2B: "afr",
        _639_3: ["afr"],
    },
    {
        _NAMES: ["Akan"],
        _639_1: "ak",
        _639_2T: "aka",
        _639_2B: "aka",
        _639_3: ["aka", "fat", "twi"],
    },
    {
        _NAMES: ["Albanian"],
        _639_1: "sq",
        _639_2T: "sqi",
        _639_2B: "alb",
        _639_3: ["sqi", "aae", "aat", "aln", "als"],
    },
    {
        _NAMES: ["Amharic"],
        _639_1: "am",
        _639_2T: "amh",
        _639_2B: "amh",
        _639_3: ["amh"],
    },
    {
        _NAMES: ["Arabic"],
        _639_1: "ar",
        _639_2T: "ara",
        _639_2B: "ara",
        _639_3: [
            "ara",
            "aao",
            "abh",
            "abv",
            "acm",
            "acq",
            "acw",
            "acx",
            "acy",
            "adf",
            "aeb",
            "aec",
            "afb",
            "ajp",
            "apc",
            "apd",
            "arb",
            "arq",
            "ars",
            "ary",
            "arz",
            "auz",
            "avl",
            "ayh",
            "ayl",
            "ayn",
            "ayp",
            "pga",
            "shu",
            "ssh",
        ],
    },
    {
        _NAMES: ["Aragonese"],
        _639_1: "an",
        _639_2T: "arg",
        _639_2B: "arg",
        _639_3: ["arg"],
    },
    {
        _NAMES: ["Armenian"],
        _639_1: "hy",
        _639_2T: "hye",
        _639_2B: "arm",
        _639_3: ["hye"],
    },
    {
        _NAMES: ["Assamese"],
        _639_1: "as",
        _639_2T: "asm",
        _639_2B: "asm",
        _639_3: ["asm"],
    },
    {
        _NAMES: ["Avaric"],
        _639_1: "av",
        _639_2T: "ava",
        _639_2B: "ava",
        _639_3: ["ava"],
    },
    {
        _NAMES: ["Avestan"],
        _639_1: "ae",
        _639_2T: "ave",
        _639_2B: "ave",
        _639_3: ["ave"],
    },
    {
        _NAMES: ["Aymara"],
        _639_1: "ay",
        _639_2T: "aym",
        _639_2B: "aym",
        _639_3: ["aym", "ayr", "ayc"],
    },
    {
        _NAMES: ["Azerbaijani"],
        _639_1: "az",
        _639_2T: "aze",
        _639_2B: "aze",
        _639_3: ["aze", "azj", "azb"],
    },
    {
        _NAMES: ["Bambara"],
        _639_1: "bm",
        _639_2T: "bam",
        _639_2B: "bam",
        _639_3: ["bam"],
    },
    {
        _NAMES: ["Bashkir"],
        _639_1: "ba",
        _639_2T: "bak",
        _639_2B: "bak",
        _639_3: ["bak"],
    },
    {
        _NAMES: ["Basque"],
        _639_1: "eu",
        _639_2T: "eus",
        _639_2B: "baq",
        _639_3: ["eus"],
    },
    {
        _NAMES: ["Belarusian"],
        _639_1: "be",
        _639_2T: "bel",
        _639_2B: "bel",
        _639_3: ["bel"],
    },
    {
        _NAMES: ["Bengali"],
        _639_1: "bn",
        _639_2T: "ben",
        _639_2B: "ben",
        _639_3: ["ben"],
    },
    {
        _NAMES: ["Bislama"],
        _639_1: "bi",
        _639_2T: "bis",
        _639_2B: "bis",
        _639_3: ["bis"],
    },
    {
        _NAMES: ["Bosnian"],
        _639_1: "bs",
        _639_2T: "bos",
        _639_2B: "bos",
        _639_3: ["bos"],
    },
    {
        _NAMES: ["Breton"],
        _639_1: "br",
        _639_2T: "bre",
        _639_2B: "bre",
        _639_3: ["bre"],
    },
    {
        _NAMES: ["Bulgarian"],
        _639_1: "bg",
        _639_2T: "bul",
        _639_2B: "bul",
        _639_3: ["bul"],
    },
    {
        _NAMES: ["Burmese"],
        _639_1: "my",
        _639_2T: "mya",
        _639_2B: "bur",
        _639_3: ["mya"],
    },
    {
        _NAMES: ["Catalan", "Valencian"],
        _639_1: "ca",
        _639_2T: "cat",
        _639_2B: "cat",
        _639_3: ["cat"],
    },
    {
        _NAMES: ["Chamorro"],
        _639_1: "ch",
        _639_2T: "cha",
        _639_2B: "cha",
        _639_3: ["cha"],
    },
    {
        _NAMES: ["Chechen"],
        _639_1: "ce",
        _639_2T: "che",
        _639_2B: "che",
        _639_3: ["che"],
    },
    {
        _NAMES: ["Chichewa", "Chewa", "Nyanja"],
        _639_1: "ny",
        _639_2T: "nya",
        _639_2B: "nya",
        _639_3: ["nya"],
    },
    {
        _NAMES: ["Chinese"],
        _639_1: "zh",
        _639_2T: "zho",
        _639_2B: "chi",
        _639_3: [
            "zho",
            "cdo",
            "cjy",
            "cmn",
            "cnp",
            "cpx",
            "csp",
            "czh",
            "czo",
            "gan",
            "hak",
            "hsn",
            "lzh",
            "mnp",
            "nan",
            "wuu",
            "yue",
        ],
    },
    {
        _NAMES: [
            "Church Slavic",
            "Old Slavonic",
            "Church Slavonic",
            "Old Bulgarian",
            "Old Church Slavonic",
        ],
        _639_1: "cu",
        _639_2T: "chu",
        _639_2B: "chu",
        _639_3: ["chu"],
    },
    {
        _NAMES: ["Chuvash"],
        _639_1: "cv",
        _639_2T: "chv",
        _639_2B: "chv",
        _639_3: ["chv"],
    },
    {
        _NAMES: ["Cornish"],
        _639_1: "kw",
        _639_2T: "cor",
        _639_2B: "cor",
        _639_3: ["cor"],
    },
    {
        _NAMES: ["Corsican"],
        _639_1: "co",
        _639_2T: "cos",
        _639_2B: "cos",
        _639_3: ["cos"],
    },
    {
        _NAMES: ["Cree"],
        _639_1: "cr",
        _639_2T: "cre",
        _639_2B: "cre",
        _639_3: ["cre", "crm", "crl", "crk", "crj", "csw", "cwd"],
    },
    {
        _NAMES: ["Croatian"],
        _639_1: "hr",
        _639_2T: "hrv",
        _639_2B: "hrv",
        _639_3: ["hrv"],
    },
    {
        _NAMES: ["Czech"],
        _639_1: "cs",
        _639_2T: "ces",
        _639_2B: "cze",
        _639_3: ["ces"],
    },
    {
        _NAMES: ["Danish"],
        _639_1: "da",
        _639_2T: "dan",
        _639_2B: "dan",
        _639_3: ["dan"],
    },
    {
        _NAMES: ["Divehi", "Dhivehi", "Maldivian"],
        _639_1: "dv",
        _639_2T: "div",
        _639_2B: "div",
        _639_3: ["div"],
    },
    {
        _NAMES: ["Dutch", "Flemish"],
        _639_1: "nl",
        _639_2T: "nld",
        _639_2B: "dut",
        _639_3: ["nld"],
    },
    {
        _NAMES: ["Dzongkha"],
        _639_1: "dz",
        _639_2T: "dzo",
        _639_2B: "dzo",
        _639_3: ["dzo"],
    },
    {
        _NAMES: ["English"],
        _639_1: "en",
        _639_2T: "eng",
        _639_2B: "eng",
        _639_3: ["eng"],
    },
    {
        _NAMES: ["Esperanto"],
        _639_1: "eo",
        _639_2T: "epo",
        _639_2B: "epo",
        _639_3: ["epo"],
    },
    {
        _NAMES: ["Estonian"],
        _639_1: "et",
        _639_2T: "est",
        _639_2B: "est",
        _639_3: ["est", "ekk", "vro"],
    },
    {
        _NAMES: ["Ewe"],
        _639_1: "ee",
        _639_2T: "ewe",
        _639_2B: "ewe",
        _639_3: ["ewe"],
    },
    {
        _NAMES: ["Faroese"],
        _639_1: "fo",
        _639_2T: "fao",
        _639_2B: "fao",
        _639_3: ["fao"],
    },
    {
        _NAMES: ["Fijian"],
        _639_1: "fj",
        _639_2T: "fij",
        _639_2B: "fij",
        _639_3: ["fij"],
    },
    {
        _NAMES: ["Finnish"],
        _639_1: "fi",
        _639_2T: "fin",
        _639_2B: "fin",
        _639_3: ["fin"],
    },
    {
        _NAMES: ["French"],
        _639_1: "fr",
        _639_2T: "fra",
        _639_2B: "fre",
        _639_3: ["fra"],
    },
    {
        _NAMES: ["Western Frisian"],
        _639_1: "fy",
        _639_2T: "fry",
        _639_2B: "fry",
        _639_3: ["fry"],
    },
    {
        _NAMES: ["Fulah"],
        _639_1: "ff",
        _639_2T: "ful",
        _639_2B: "ful",
        _639_3: ["ful", "fub", "fui", "fue", "fuq", "ffm", "fuv", "fuc", "fuf", "fuh"],
    },
    {
        _NAMES: ["Gaelic", "Scottish Gaelic"],
        _639_1: "gd",
        _639_2T: "gla",
        _639_2B: "gla",
        _639_3: ["gla"],
    },
    {
        _NAMES: ["Galician"],
        _639_1: "gl",
        _639_2T: "glg",
        _639_2B: "glg",
        _639_3: ["glg"],
    },
    {
        _NAMES: ["Ganda"],
        _639_1: "lg",
        _639_2T: "lug",
        _639_2B: "lug",
        _639_3: ["lug"],
    },
    {
        _NAMES: ["Georgian"],
        _639_1: "ka",
        _639_2T: "kat",
        _639_2B: "geo",
        _639_3: ["kat"],
    },
    {
        _NAMES: ["German"],
        _639_1: "de",
        _639_2T: "deu",
        _639_2B: "ger",
        _639_3: ["deu"],
    },
    {
        _NAMES: ["Greek", "Modern (1453–)"],
        _639_1: "el",
        _639_2T: "ell",
        _639_2B: "gre",
        _639_3: ["ell"],
    },
    {
        _NAMES: ["Kalaallisut", "Greenlandic"],
        _639_1: "kl",
        _639_2T: "kal",
        _639_2B: "kal",
        _639_3: ["kal"],
    },
    {
        _NAMES: ["Guarani"],
        _639_1: "gn",
        _639_2T: "grn",
        _639_2B: "grn",
        _639_3: ["grn", "nhd", "gui", "gun", "gug", "gnw"],
    },
    {
        _NAMES: ["Gujarati"],
        _639_1: "gu",
        _639_2T: "guj",
        _639_2B: "guj",
        _639_3: ["guj"],
    },
    {
        _NAMES: ["Haitian", "Haitian Creole"],
        _639_1: "ht",
        _639_2T: "hat",
        _639_2B: "hat",
        _639_3: ["hat"],
    },
    {
        _NAMES: ["Hausa"],
        _639_1: "ha",
        _639_2T: "hau",
        _639_2B: "hau",
        _639_3: ["hau"],
    },
    {
        _NAMES: ["Hebrew"],
        _639_1: "he",
        _639_2T: "heb",
        _639_2B: "heb",
        _639_3: ["heb"],
    },
    {
        _NAMES: ["Herero"],
        _639_1: "hz",
        _639_2T: "her",
        _639_2B: "her",
        _639_3: ["her"],
    },
    {
        _NAMES: ["Hindi"],
        _639_1: "hi",
        _639_2T: "hin",
        _639_2B: "hin",
        _639_3: ["hin"],
    },
    {
        _NAMES: ["Hiri Motu"],
        _639_1: "ho",
        _639_2T: "hmo",
        _639_2B: "hmo",
        _639_3: ["hmo"],
    },
    {
        _NAMES: ["Hungarian"],
        _639_1: "hu",
        _639_2T: "hun",
        _639_2B: "hun",
        _639_3: ["hun"],
    },
    {
        _NAMES: ["Icelandic"],
        _639_1: "is",
        _639_2T: "isl",
        _639_2B: "ice",
        _639_3: ["isl"],
    },
    {
        _NAMES: ["Ido"],
        _639_1: "io",
        _639_2T: "ido",
        _639_2B: "ido",
        _639_3: ["ido"],
    },
    {
        _NAMES: ["Igbo"],
        _639_1: "ig",
        _639_2T: "ibo",
        _639_2B: "ibo",
        _639_3: ["ibo"],
    },
    {
        _NAMES: ["Indonesian"],
        _639_1: "id",
        _639_2T: "ind",
        _639_2B: "ind",
        _639_3: ["ind"],
    },
    {
        _NAMES: ["Interlingua (International Auxiliary Language Association)"],
        _639_1: "ia",
        _639_2T: "ina",
        _639_2B: "ina",
        _639_3: ["ina"],
    },
    {
        _NAMES: ["Interlingue", "Occidental"],
        _639_1: "ie",
        _639_2T: "ile",
        _639_2B: "ile",
        _639_3: ["ile"],
    },
    {
        _NAMES: ["Inuktitut"],
        _639_1: "iu",
        _639_2T: "iku",
        _639_2B: "iku",
        _639_3: ["iku", "ike", "ikt"],
    },
    {
        _NAMES: ["Inupiaq"],
        _639_1: "ik",
        _639_2T: "ipk",
        _639_2B: "ipk",
        _639_3: ["ipk", "esi", "esk"],
    },
    {
        _NAMES: ["Irish"],
        _639_1: "ga",
        _639_2T: "gle",
        _639_2B: "gle",
        _639_3: ["gle"],
    },
    {
        _NAMES: ["Italian"],
        _639_1: "it",
        _639_2T: "ita",
        _639_2B: "ita",
        _639_3: ["ita"],
    },
    {
        _NAMES: ["Japanese"],
        _639_1: "ja",
        _639_2T: "jpn",
        _639_2B: "jpn",
        _639_3: ["jpn"],
    },
    {
        _NAMES: ["Javanese"],
        _639_1: "jv",
        _639_2T: "jav",
        _639_2B: "jav",
        _639_3: ["jav"],
    },
    {
        _NAMES: ["Kannada"],
        _639_1: "kn",
        _639_2T: "kan",
        _639_2B: "kan",
        _639_3: ["kan"],
    },
    {
        _NAMES: ["Kanuri"],
        _639_1: "kr",
        _639_2T: "kau",
        _639_2B: "kau",
        _639_3: ["kau", "knc", "kby", "krt"],
    },
    {
        _NAMES: ["Kashmiri"],
        _639_1: "ks",
        _639_2T: "kas",
        _639_2B: "kas",
        _639_3: ["kas"],
    },
    {
        _NAMES: ["Kazakh"],
        _639_1: "kk",
        _639_2T: "kaz",
        _639_2B: "kaz",
        _639_3: ["kaz"],
    },
    {
        _NAMES: ["Central Khmer"],
        _639_1: "km",
        _639_2T: "khm",
        _639_2B: "khm",
        _639_3: ["khm"],
    },
    {
        _NAMES: ["Kikuyu", "Gikuyu"],
        _639_1: "ki",
        _639_2T: "kik",
        _639_2B: "kik",
        _639_3: ["kik"],
    },
    {
        _NAMES: ["Kinyarwanda"],
        _639_1: "rw",
        _639_2T: "kin",
        _639_2B: "kin",
        _639_3: ["kin"],
    },
    {
        _NAMES: ["Kirghiz", "Kyrgyz"],
        _639_1: "ky",
        _639_2T: "kir",
        _639_2B: "kir",
        _639_3: ["kir"],
    },
    {
        _NAMES: ["Komi"],
        _639_1: "kv",
        _639_2T: "kom",
        _639_2B: "kom",
        _639_3: ["kom", "koi", "kpv"],
    },
    {
        _NAMES: ["Kongo"],
        _639_1: "kg",
        _639_2T: "kon",
        _639_2B: "kon",
        _639_3: ["kon", "kng", "ldi", "kwy"],
    },
    {
        _NAMES: ["Korean"],
        _639_1: "ko",
        _639_2T: "kor",
        _639_2B: "kor",
        _639_3: ["kor"],
    },
    {
        _NAMES: ["Kuanyama", "Kwanyama"],
        _639_1: "kj",
        _639_2T: "kua",
        _639_2B: "kua",
        _639_3: ["kua"],
    },
    {
        _NAMES: ["Kurdish"],
        _639_1: "ku",
        _639_2T: "kur",
        _639_2B: "kur",
        _639_3: ["kur", "ckb", "kmr", "sdh"],
    },
    {
        _NAMES: ["Lao"],
        _639_1: "lo",
        _639_2T: "lao",
        _639_2B: "lao",
        _639_3: ["lao"],
    },
    {
        _NAMES: ["Latin"],
        _639_1: "la",
        _639_2T: "lat",
        _639_2B: "lat",
        _639_3: ["lat"],
    },
    {
        _NAMES: ["Latvian"],
        _639_1: "lv",
        _639_2T: "lav",
        _639_2B: "lav",
        _639_3: ["lav", "ltg", "lvs"],
    },
    {
        _NAMES: ["Limburgan", "Limburger", "Limburgish"],
        _639_1: "li",
        _639_2T: "lim",
        _639_2B: "lim",
        _639_3: ["lim"],
    },
    {
        _NAMES: ["Lingala"],
        _639_1: "ln",
        _639_2T: "lin",
        _639_2B: "lin",
        _639_3: ["lin"],
    },
    {
        _NAMES: ["Lithuanian"],
        _639_1: "lt",
        _639_2T: "lit",
        _639_2B: "lit",
        _639_3: ["lit"],
    },
    {
        _NAMES: ["Luba-Katanga"],
        _639_1: "lu",
        _639_2T: "lub",
        _639_2B: "lub",
        _639_3: ["lub"],
    },
    {
        _NAMES: ["Luxembourgish", "Letzeburgesch"],
        _639_1: "lb",
        _639_2T: "ltz",
        _639_2B: "ltz",
        _639_3: ["ltz"],
    },
    {
        _NAMES: ["Macedonian"],
        _639_1: "mk",
        _639_2T: "mkd",
        _639_2B: "mac",
        _639_3: ["mkd"],
    },
    {
        _NAMES: ["Malagasy"],
        _639_1: "mg",
        _639_2T: "mlg",
        _639_2B: "mlg",
        _639_3: [
            "mlg",
            "xmv",
            "bhr",
            "msh",
            "bmm",
            "plt",
            "skg",
            "bzc",
            "tkg",
            "tdx",
            "txy",
            "xmw",
        ],
    },
    {
        _NAMES: ["Malay"],
        _639_1: "ms",
        _639_2T: "msa",
        _639_2B: "may",
        _639_3: [
            "msa",
            "btj",
            "mfb",
            "bjn",
            "bve",
            "kxd",
            "bvu",
            "pse",
            "coa",
            "liw",
            "dup",
            "hji",
            "ind",
            "jak",
            "jax",
            "vkk",
            "meo",
            "kvr",
            "mqg",
            "kvb",
            "lce",
            "lcf",
            "zlm",
            "xmm",
            "min",
            "mui",
            "zmi",
            "max",
            "orn",
            "ors",
            "mfa",
            "pel",
            "msi",
            "zsm",
            "tmw",
            "vkt",
            "urk",
        ],
    },
    {
        _NAMES: ["Malayalam"],
        _639_1: "ml",
        _639_2T: "mal",
        _639_2B: "mal",
        _639_3: ["mal"],
    },
    {
        _NAMES: ["Maltese"],
        _639_1: "mt",
        _639_2T: "mlt",
        _639_2B: "mlt",
        _639_3: ["mlt"],
    },
    {
        _NAMES: ["Manx"],
        _639_1: "gv",
        _639_2T: "glv",
        _639_2B: "glv",
        _639_3: ["glv"],
    },
    {
        _NAMES: ["Maori"],
        _639_1: "mi",
        _639_2T: "mri",
        _639_2B: "mao",
        _639_3: ["mri"],
    },
    {
        _NAMES: ["Marathi"],
        _639_1: "mr",
        _639_2T: "mar",
        _639_2B: "mar",
        _639_3: ["mar"],
    },
    {
        _NAMES: ["Marshallese"],
        _639_1: "mh",
        _639_2T: "mah",
        _639_2B: "mah",
        _639_3: ["mah"],
    },
    {
        _NAMES: ["Mongolian"],
        _639_1: "mn",
        _639_2T: "mon",
        _639_2B: "mon",
        _639_3: ["mon", "khk", "mvf"],
    },
    {
        _NAMES: ["Nauru"],
        _639_1: "na",
        _639_2T: "nau",
        _639_2B: "nau",
        _639_3: ["nau"],
    },
    {
        _NAMES: ["Navajo", "Navaho"],
        _639_1: "nv",
        _639_2T: "nav",
        _639_2B: "nav",
        _639_3: ["nav"],
    },
    {
        _NAMES: ["North Ndebele"],
        _639_1: "nd",
        _639_2T: "nde",
        _639_2B: "nde",
        _639_3: ["nde"],
    },
    {
        _NAMES: ["South Ndebele"],
        _639_1: "nr",
        _639_2T: "nbl",
        _639_2B: "nbl",
        _639_3: ["nbl"],
    },
    {
        _NAMES: ["Ndonga"],
        _639_1: "ng",
        _639_2T: "ndo",
        _639_2B: "ndo",
        _639_3: ["ndo"],
    },
    {
        _NAMES: ["Nepali"],
        _639_1: "ne",
        _639_2T: "nep",
        _639_2B: "nep",
        _639_3: ["nep", "dty", "npi"],
    },
    {
        _NAMES: ["Norwegian"],
        _639_1: "no",
        _639_2T: "nor",
        _639_2B: "nor",
        _639_3: ["nor", "nob", "nno"],
    },
    {
        _NAMES: ["Sichuan Yi", "Nuosu"],
        _639_1: "ii",
        _639_2T: "iii",
        _639_2B: "iii",
        _639_3: ["iii"],
    },
    {
        _NAMES: ["Occitan"],
        _639_1: "oc",
        _639_2T: "oci",
        _639_2B: "oci",
        _639_3: ["oci"],
    },
    {
        _NAMES: ["Ojibwa"],
        _639_1: "oj",
        _639_2T: "oji",
        _639_2B: "oji",
        _639_3: ["oji", "ciw", "ojb", "ojc", "ojg", "ojs", "ojw", "otw"],
    },
    {
        _NAMES: ["Oriya"],
        _639_1: "or",
        _639_2T: "ori",
        _639_2B: "ori",
        _639_3: ["ori", "ory", "spv"],
    },
    {
        _NAMES: ["Oromo"],
        _639_1: "om",
        _639_2T: "orm",
        _639_2B: "orm",
        _639_3: ["orm", "gax", "hae", "orc", "gaz"],
    },
    {
        _NAMES: ["Ossetian", "Ossetic"],
        _639_1: "os",
        _639_2T: "oss",
        _639_2B: "oss",
        _639_3: ["oss"],
    },
    {
        _NAMES: ["Pali"],
        _639_1: "pi",
        _639_2T: "pli",
        _639_2B: "pli",
        _639_3: ["pli"],
    },
    {
        _NAMES: ["Pashto", "Pushto"],
        _639_1: "ps",
        _639_2T: "pus",
        _639_2B: "pus",
        _639_3: ["pus", "pst", "pbu", "pbt"],
    },
    {
        _NAMES: ["Persian"],
        _639_1: "fa",
        _639_2T: "fas",
        _639_2B: "per",
        _639_3: ["fas", "prs", "pes"],
    },
    {
        _NAMES: ["Polish"],
        _639_1: "pl",
        _639_2T: "pol",
        _639_2B: "pol",
        _639_3: ["pol"],
    },
    {
        _NAMES: ["Portuguese"],
        _639_1: "pt",
        _639_2T: "por",
        _639_2B: "por",
        _639_3: ["por"],
    },
    {
        _NAMES: ["Punjabi", "Panjabi"],
        _639_1: "pa",
        _639_2T: "pan",
        _639_2B: "pan",
        _639_3: ["pan"],
    },
    {
        _NAMES: ["Quechua"],
        _639_1: "qu",
        _639_2T: "que",
        _639_2B: "que",
        _639_3: [
            "que",
            "qva",
            "qxu",
            "quy",
            "qvc",
            "qvl",
            "qud",
            "qxr",
            "quk",
            "qug",
            "qxc",
            "qxa",
            "qwc",
            "qwa",
            "quz",
            "qve",
            "qub",
            "qvh",
            "qwh",
            "qvw",
            "qvi",
            "qxw",
            "quf",
            "qvj",
            "qvm",
            "qvo",
            "qul",
            "qvn",
            "qxn",
            "qvz",
            "qvp",
            "qxh",
            "qxp",
            "qxl",
            "qvs",
            "qxt",
            "qus",
            "qws",
            "quh",
            "qxo",
            "qup",
            "quw",
            "qur",
            "qux",
        ],
    },
    {
        _NAMES: ["Romanian", "Moldavian", "Moldovan"],
        _639_1: "ro",
        _639_2T: "ron",
        _639_2B: "rum",
        _639_3: ["ron"],
    },
    {
        _NAMES: ["Romansh"],
        _639_1: "rm",
        _639_2T: "roh",
        _639_2B: "roh",
        _639_3: ["roh"],
    },
    {
        _NAMES: ["Rundi"],
        _639_1: "rn",
        _639_2T: "run",
        _639_2B: "run",
        _639_3: ["run"],
    },
    {
        _NAMES: ["Russian"],
        _639_1: "ru",
        _639_2T: "rus",
        _639_2B: "rus",
        _639_3: ["rus"],
    },
    {
        _NAMES: ["Northern Sami"],
        _639_1: "se",
        _639_2T: "sme",
        _639_2B: "sme",
        _639_3: ["sme"],
    },
    {
        _NAMES: ["Samoan"],
        _639_1: "sm",
        _639_2T: "smo",
        _639_2B: "smo",
        _639_3: ["smo"],
    },
    {
        _NAMES: ["Sango"],
        _639_1: "sg",
        _639_2T: "sag",
        _639_2B: "sag",
        _639_3: ["sag"],
    },
    {
        _NAMES: ["Sanskrit"],
        _639_1: "sa",
        _639_2T: "san",
        _639_2B: "san",
        _639_3: ["san"],
    },
    {
        _NAMES: ["Sardinian"],
        _639_1: "sc",
        _639_2T: "srd",
        _639_2B: "srd",
        _639_3: ["srd", "sro", "sdn", "src", "sdc"],
    },
    {
        _NAMES: ["Serbian"],
        _639_1: "sr",
        _639_2T: "srp",
        _639_2B: "srp",
        _639_3: ["srp"],
    },
    {
        _NAMES: ["Shona"],
        _639_1: "sn",
        _639_2T: "sna",
        _639_2B: "sna",
        _639_3: ["sna"],
    },
    {
        _NAMES: ["Sindhi"],
        _639_1: "sd",
        _639_2T: "snd",
        _639_2B: "snd",
        _639_3: ["snd"],
    },
    {
        _NAMES: ["Sinhala", "Sinhalese"],
        _639_1: "si",
        _639_2T: "sin",
        _639_2B: "sin",
        _639_3: ["sin"],
    },
    {
        _NAMES: ["Slovak"],
        _639_1: "sk",
        _639_2T: "slk",
        _639_2B: "slo",
        _639_3: ["slk"],
    },
    {
        _NAMES: ["Slovenian"],
        _639_1: "sl",
        _639_2T: "slv",
        _639_2B: "slv",
        _639_3: ["slv"],
    },
    {
        _NAMES: ["Somali"],
        _639_1: "so",
        _639_2T: "som",
        _639_2B: "som",
        _639_3: ["som"],
    },
    {
        _NAMES: ["Southern Sotho"],
        _639_1: "st",
        _639_2T: "sot",
        _639_2B: "sot",
        _639_3: ["sot"],
    },
    {
        _NAMES: ["Spanish", "Castilian"],
        _639_1: "es",
        _639_2T: "spa",
        _639_2B: "spa",
        _639_3: ["spa"],
    },
    {
        _NAMES: ["Sundanese"],
        _639_1: "su",
        _639_2T: "sun",
        _639_2B: "sun",
        _639_3: ["sun"],
    },
    {
        _NAMES: ["Swahili"],
        _639_1: "sw",
        _639_2T: "swa",
        _639_2B: "swa",
        _639_3: ["swa", "swc", "swh"],
    },
    {
        _NAMES: ["Swati"],
        _639_1: "ss",
        _639_2T: "ssw",
        _639_2B: "ssw",
        _639_3: ["ssw"],
    },
    {
        _NAMES: ["Swedish"],
        _639_1: "sv",
        _639_2T: "swe",
        _639_2B: "swe",
        _639_3: ["swe"],
    },
    {
        _NAMES: ["Tagalog"],
        _639_1: "tl",
        _639_2T: "tgl",
        _639_2B: "tgl",
        _639_3: ["tgl"],
    },
    {
        _NAMES: ["Tahitian"],
        _639_1: "ty",
        _639_2T: "tah",
        _639_2B: "tah",
        _639_3: ["tah"],
    },
    {
        _NAMES: ["Tajik"],
        _639_1: "tg",
        _639_2T: "tgk",
        _639_2B: "tgk",
        _639_3: ["tgk"],
    },
    {
        _NAMES: ["Tamil"],
        _639_1: "ta",
        _639_2T: "tam",
        _639_2B: "tam",
        _639_3: ["tam"],
    },
    {
        _NAMES: ["Tatar"],
        _639_1: "tt",
        _639_2T: "tat",
        _639_2B: "tat",
        _639_3: ["tat"],
    },
    {
        _NAMES: ["Telugu"],
        _639_1: "te",
        _639_2T: "tel",
        _639_2B: "tel",
        _639_3: ["tel"],
    },
    {
        _NAMES: ["Thai"],
        _639_1: "th",
        _639_2T: "tha",
        _639_2B: "tha",
        _639_3: ["tha"],
    },
    {
        _NAMES: ["Tibetan"],
        _639_1: "bo",
        _639_2T: "bod",
        _639_2B: "tib",
        _639_3: ["bod"],
    },
    {
        _NAMES: ["Tigrinya"],
        _639_1: "ti",
        _639_2T: "tir",
        _639_2B: "tir",
        _639_3: ["tir"],
    },
    {
        _NAMES: ["Tonga (Tonga Islands)"],
        _639_1: "to",
        _639_2T: "ton",
        _639_2B: "ton",
        _639_3: ["ton"],
    },
    {
        _NAMES: ["Tsonga"],
        _639_1: "ts",
        _639_2T: "tso",
        _639_2B: "tso",
        _639_3: ["tso"],
    },
    {
        _NAMES: ["Tswana"],
        _639_1: "tn",
        _639_2T: "tsn",
        _639_2B: "tsn",
        _639_3: ["tsn"],
    },
    {
        _NAMES: ["Turkish"],
        _639_1: "tr",
        _639_2T: "tur",
        _639_2B: "tur",
        _639_3: ["tur"],
    },
    {
        _NAMES: ["Turkmen"],
        _639_1: "tk",
        _639_2T: "tuk",
        _639_2B: "tuk",
        _639_3: ["tuk"],
    },
    {
        _NAMES: ["Twi"],
        _639_1: "tw",
        _639_2T: "twi",
        _639_2B: "twi",
        _639_3: ["twi"],
    },
    {
        _NAMES: ["Uighur", "Uyghur"],
        _639_1: "ug",
        _639_2T: "uig",
        _639_2B: "uig",
        _639_3: ["uig"],
    },
    {
        _NAMES: ["Ukrainian"],
        _639_1: "uk",
        _639_2T: "ukr",
        _639_2B: "ukr",
        _639_3: ["ukr"],
    },
    {
        _NAMES: ["Urdu"],
        _639_1: "ur",
        _639_2T: "urd",
        _639_2B: "urd",
        _639_3: ["urd"],
    },
    {
        _NAMES: ["Uzbek"],
        _639_1: "uz",
        _639_2T: "uzb",
        _639_2B: "uzb",
        _639_3: ["uzb", "uzn", "uzs"],
    },
    {
        _NAMES: ["Venda"],
        _639_1: "ve",
        _639_2T: "ven",
        _639_2B: "ven",
        _639_3: ["ven"],
    },
    {
        _NAMES: ["Vietnamese"],
        _639_1: "vi",
        _639_2T: "vie",
        _639_2B: "vie",
        _639_3: ["vie"],
    },
    {
        _NAMES: ["Volapük"],
        _639_1: "vo",
        _639_2T: "vol",
        _639_2B: "vol",
        _639_3: ["vol"],
    },
    {
        _NAMES: ["Walloon"],
        _639_1: "wa",
        _639_2T: "wln",
        _639_2B: "wln",
        _639_3: ["wln"],
    },
    {
        _NAMES: ["Welsh"],
        _639_1: "cy",
        _639_2T: "cym",
        _639_2B: "wel",
        _639_3: ["cym"],
    },
    {
        _NAMES: ["Wolof"],
        _639_1: "wo",
        _639_2T: "wol",
        _639_2B: "wol",
        _639_3: ["wol"],
    },
    {
        _NAMES: ["Xhosa"],
        _639_1: "xh",
        _639_2T: "xho",
        _639_2B: "xho",
        _639_3: ["xho"],
    },
    {
        _NAMES: ["Yiddish"],
        _639_1: "yi",
        _639_2T: "yid",
        _639_2B: "yid",
        _639_3: ["yid", "ydd", "yih"],
    },
    {
        _NAMES: ["Yoruba"],
        _639_1: "yo",
        _639_2T: "yor",
        _639_2B: "yor",
        _639_3: ["yor"],
    },
    {
        _NAMES: ["Zhuang", "Chuang"],
        _639_1: "za",
        _639_2T: "zha",
        _639_2B: "zha",
        _639_3: [
            "zha",
            "zch",
            "zhd",
            "zeh",
            "zgb",
            "zgn",
            "zln",
            "zlj",
            "zlq",
            "zgm",
            "zhn",
            "zqe",
            "zyg",
            "zyb",
            "zyn",
            "zyj",
            "zzj",
        ],
    },
    {
        _NAMES: ["Zulu"],
        _639_1: "zu",
        _639_2T: "zul",
        _639_2B: "zul",
        _639_3: ["zul"],
    },
]

LANGUAGES_BY_NAMES = {
    key.casefold(): lang for lang in LANGUAGES for key in lang[_NAMES]
}
LANGUAGES_BY_639_1 = {lang[_639_1]: lang for lang in LANGUAGES}
LANGUAGES_BY_639_2T = {lang[_639_2T]: lang for lang in LANGUAGES}
LANGUAGES_BY_639_2B = {lang[_639_2B]: lang for lang in LANGUAGES}
LANGUAGES_BY_639_3 = {
    key.casefold(): lang for lang in LANGUAGES for key in lang[_639_3]
}

LANGUAGES_INDEXED_BY = {
    _NAMES: LANGUAGES_BY_NAMES,
    _639_1: LANGUAGES_BY_639_1,
    _639_2T: LANGUAGES_BY_639_2T,
    _639_2B: LANGUAGES_BY_639_2B,
    _639_3: LANGUAGES_BY_639_3,
}
