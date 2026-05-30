import json
import os

concept_blocks = [
  {
    "block_id": "CB1",
    "title": "Subject Nouns Semantic Shifts & Advice vs Advise Rules",
    "transcript_range_percent": [0, 20],
    "explanation": "This section covers subject nouns ending in 's' and the distinction between the noun 'advice' and the verb 'advise'. Nouns representing academic disciplines (e.g., Physics, Economics, Statistics, Politics, Ethics) are treated as singular nouns when representing the subject as a whole (e.g., 'Economics is interesting'). However, they undergo a semantic shift and become plural when referring to political/economic ideas, views, data, or behaviors (e.g., 'The politics of the candidates are different'). Additionally, 'advise' is a verb with inflected forms (advised), whereas 'advice' is an uncountable noun. It can never take an indefinite article 'an' or be pluralized as 'advices' in standard English; instead, use 'a piece of advice' or 'words of advice'. An exception is the commercial usage of 'advices' in business correspondence meaning 'official notifications' (e.g., 'the advices regarding your purchase').",
    "examples": [
      {
        "sentence": "Economics is an interesting topic, but the economics of the two leaders are rooted in different philosophies.",
        "rule": "Subject nouns are singular as disciplines but plural when denoting policies or ideas.",
        "working": "Economics (discipline) -> is (singular) | the economics (policies) -> are (plural)."
      },
      {
        "sentence": "My father gave me a piece of advice rather than giving me multiple advices.",
        "rule": "Advice is an uncountable noun; do not use 'an advice' or 'advices' (use 'a piece of advice' or 'words of advice').",
        "working": "an advice -> incorrect -> change to 'a piece of advice' | advices -> incorrect -> change to 'words of advice'."
      },
      {
        "sentence": "Our office has sent you the advices with regard to your purchase.",
        "rule": "In official commercial correspondence, 'advices' can be used as a plural noun meaning business notifications.",
        "working": "advices -> plural business notifications -> grammatically correct in this specific commercial context."
      }
    ],
    "exercise_questions": [1, 2, 3],
    "visual_moments": [
      {
        "timestamp": "00:04:30",
        "type": "board",
        "description": "Board chart listing singular disciplines (Physics, Politics) vs their plural semantic shifts (ideas, policies) and advice/advise differences."
      }
    ],
    "teacher_quotes": [
      "Economics is an interesting topic... देखने में बेशक आपको ये plural लगते हैं... but reality में हम इनको singular की तरह ही use करते हैं।",
      "Advices to this effect... In official business letter, we are sending you the advices."
    ],
    "traps": [
      "Never use 'an advice' or 'advised' with 'c' spelling; 'advice' is the noun and 'advise' is the verb."
    ],
    "tricks": [
      "Advise = Verb (action). Advice = Noun (the thing). Business exception: Advices = commercial notifications."
    ]
  },
  {
    "block_id": "CB2",
    "title": "Hyphenated Compound Measures & Primary Noun Pluralization",
    "transcript_range_percent": [20, 48],
    "explanation": "This block covers the formatting of compound numerical modifiers and the rules for pluralizing compound nouns. When a number and a unit of measurement combine to modify a subsequent noun, the unit must remain singular and is typically hyphenated (e.g., 'a ten-rupee note' not rupees, 'a five-minute break' not minutes, 'a ten-mile race', 'a five-year plan'). Second, when pluralizing compound nouns formed with prepositions (such as 'commander-in-chief'), pluralize the principal or head noun rather than the final modifier (e.g., 'commanders-in-chief' not commander-in-chiefs, 'professors-in-charge'). Finally, nouns like fish, deer, sheep, and hair have identical singular and plural forms; adding an 's' (e.g., sheeps, deers) is incorrect.",
    "examples": [
      {
        "sentence": "The runner finished a ten-mile race and then took a five-minute break.",
        "rule": "Units in compound numerical modifiers acting as adjectives must remain singular.",
        "working": "ten miles race -> compound modifier -> change to 'ten-mile race' | five minutes break -> change to 'five-minute break'."
      },
      {
        "sentence": "The commanders-in-chief and the professors-in-charge met at the conference.",
        "rule": "Pluralize the principal head noun in prepositional compound nouns, not the final word.",
        "working": "commander-in-chiefs -> incorrect -> change to 'commanders-in-chief' | professor-in-charges -> change to 'professors-in-charge'."
      }
    ],
    "exercise_questions": [4, 5],
    "visual_moments": [
      {
        "timestamp": "00:16:30",
        "type": "board",
        "description": "List of hyphenated measurement phrases (ten-rupee, five-minute) and compound plural rules (commanders-in-chief) on the board."
      }
    ],
    "teacher_quotes": [
      "100 metre race कहा जाएगा... a ten rupee note, rupees नहीं... We were given a five minute break, not minutes.",
      "Commanders-in-chief... Professors-in-charge... Pluralize the principal word."
    ],
    "traps": [
      "Do not pluralize the unit in adjectival phrases; do not write 'commander-in-chiefs' or 'sheeps'."
    ],
    "tricks": [
      "Modifier: Number + Singular Unit + Noun (e.g., a ten-year plan)."
    ]
  },
  {
    "block_id": "CB3",
    "title": "Fraction/Percentage Quantifiers & Inanimate Possessives",
    "transcript_range_percent": [48, 62],
    "explanation": "This block discusses rules for subject-verb agreement with fractional or percentage quantifiers, and the restriction on possessive apostrophes for non-living entities. First, when a subject contains a fraction or percentage (e.g., 'one third of...', 'four fifths of...'), the verb's number agrees with the noun following the preposition 'of'. If the subsequent noun is uncountable, the verb is singular ('one third of the milk has been exhausted'). If the noun is singular countable, the verb is singular ('four fifths of the task was finished'). If the noun is plural countable, the verb is plural ('one third of the books have been destroyed'). Second, do not use the possessive apostrophe 's' for non-living, inanimate objects; instead, use the prepositional 'of' construction (e.g., 'the legs of the table' instead of 'the table's legs', 'the pages of the book' instead of 'the book's pages').",
    "examples": [
      {
        "sentence": "One third of the milk has been exhausted, but three fourths of the boys have agreed to go.",
        "rule": "For fractions/percentages, the verb agrees with the noun following 'of'.",
        "working": "one third of the milk (uncountable) -> has (singular) | three fourths of the boys (plural count) -> have (plural)."
      },
      {
        "sentence": "The legs of the table are broken and the pages of the book are torn.",
        "rule": "Use the 'of' construction for possessives of inanimate, non-living objects instead of apostrophe 's'.",
        "working": "table's legs -> non-living -> change to 'legs of the table' | book's pages -> change to 'pages of the book'."
      }
    ],
    "exercise_questions": [6, 7],
    "visual_moments": [
      {
        "timestamp": "00:38:30",
        "type": "board",
        "description": "Fractions agreement rules (milk vs books) and animate vs inanimate possessive examples on the board."
      }
    ],
    "teacher_quotes": [
      "one third of the milk has... countable noun... one third of the books have been destroyed.",
      "The legs of my table are broken... We never say my table's legs are broken. Use legs of the table."
    ],
    "traps": [
      "Do not write 'the table's legs' or use plural verbs for fractions of uncountable nouns."
    ],
    "tricks": [
      "Fractions rule: Focus strictly on the noun after 'of' to determine singular vs plural agreement."
    ]
  },
  {
    "block_id": "CB4",
    "title": "Abstract Nouns Article Omission vs Single/Double Article Meanings",
    "transcript_range_percent": [62, 85],
    "explanation": "This section covers the omission of articles before abstract nouns and the distinction between single and double articles with multiple nouns. First, abstract nouns (e.g., freedom, cleanliness, justice, truth, love) omit articles when used in a generic, universal, or abstract sense (e.g., 'Cleanliness is next to godliness'). However, they require the definite article 'the' when they are contextualized, specified, or restricted to a particular situation (e.g., 'The justice delivered in this case is a mockery'). Second, when two nouns are connected by 'and', prefixing only the first noun with a definite article indicates a single individual possessing both roles, taking a singular verb (e.g., 'The poet and politician was sitting...'). Prefixing both nouns with 'the' indicates two separate individuals, taking a plural verb (e.g., 'The poet and the politician were sitting...').",
    "examples": [
      {
        "sentence": "Cleanliness is next to godliness, but the justice delivered in this case is a mockery.",
        "rule": "Generic abstract nouns take no article; specific contextualized abstract nouns require 'the'.",
        "working": "Cleanliness (generic) -> no article | justice (specific to this case) -> prefix with 'the'."
      },
      {
        "sentence": "The famous poet and politician was sitting in the front row, whereas the poet and the politician were arguing.",
        "rule": "Single article = one person (singular verb); double articles = two separate people (plural verb).",
        "working": "The poet and politician -> one person -> was (singular) | The poet and the politician -> two people -> were (plural)."
      }
    ],
    "exercise_questions": [8, 9],
    "visual_moments": [
      {
        "timestamp": "00:45:00",
        "type": "board",
        "description": "Abstract nouns article comparison chart and poet/politician double article diagrams."
      }
    ],
    "teacher_quotes": [
      "cleanliness is next to godliness... general way में the की कोई जरूरत नहीं। The freedom won by India... special case.",
      "The poet and politician... means one person. The poet and the politician means two people."
    ],
    "traps": [
      "Do not add 'the' to generic proverbs; do not use plural verbs for single individuals possessing double titles."
    ],
    "tricks": [
      "Single 'The' = Single person (singular verb). Double 'The' = Double persons (plural verb)."
    ]
  },
  {
    "block_id": "CB5",
    "title": "Work/Works & Force/Forces Polysemous Nouns & Joint Possessives",
    "transcript_range_percent": [85, 100],
    "explanation": "This block covers polysemous nouns that change meaning when pluralized, and the apostrophe 's' rules for joint vs. separate possessives. First, 'work' refers to labor/effort and is uncountable ('much work to do', never 'works'). However, 'works' represents literary/artistic masterpieces ('Shakespeare's works') or a factory/industrial plant ('its works are in Jamnagar'). Similarly, 'force' denotes physical strength/gravity, whereas 'forces' represents military troops or police reinforcements ('forces were rushed'). Second, essential items are pluralized as 'goods' ('essential goods are costly'). Third, when expressing possessives for joint ownership, place the apostrophe 's' on the last name only, taking a singular noun and verb (e.g., 'Changu and Mangu's workshop is...'). For separate ownership, place the apostrophe on both names, taking a plural noun and verb (e.g., 'Changu's and Mangu's workshops are...').",
    "examples": [
      {
        "sentence": "I have got much work to do, but many of Shakespeare's works have been translated into Punjabi.",
        "rule": "Work (labor) is uncountable; works (literary/artistic pieces or industrial plants) is countable/plural.",
        "working": "many works to do -> labor -> change to 'much work to do' or 'pieces of work' | Shakespeare's works -> literary pieces -> correct."
      },
      {
        "sentence": "The government rushed more forces to the border where the force of gravity is constant.",
        "rule": "Force means strength (singular); forces means military or police troops (plural).",
        "working": "rushed force -> troops -> change to 'forces' | force of gravity -> strength -> correct."
      },
      {
        "sentence": "Changu and Mangu's workshop is located in the market, but Changu's and Mangu's workshops are separated.",
        "rule": "Joint possessives use apostrophe 's' on the last name (singular); separate possessives use apostrophe on both names (plural).",
        "working": "Changu's and Mangu's workshop is -> separate shops -> change to 'Changu's and Mangu's workshops are'."
      }
    ],
    "exercise_questions": [10, 11, 12],
    "visual_moments": [
      {
        "timestamp": "00:58:30",
        "type": "board",
        "description": "Polysemous noun shifts columns (work/works, force/forces) and joint vs separate ownership diagrams."
      }
    ],
    "teacher_quotes": [
      "I have many works to do... patently wrong... I have got a piece of work... much work to do.",
      "Many of Shakespeare's works... Rehman's works... Jamnagar works.",
      "Changu and Mangu's workshop... joint vs separate."
    ],
    "traps": [
      "Do not use 'works' to mean labor/chores; do not use singular verbs for separate possessives."
    ],
    "tricks": [
      "Labor = Work (Uncountable). Art/Industrial = Works (Countable). Troops = Forces (Plural)."
    ]
  }
]

frame_manifest = {
  "CB1_1.jpg": {
    "timestamp": "00:04:30",
    "ocr_text": "Physics, Politics, Statistics, Ethics singular vs plural shifts, advice vs advise...",
    "type": "board"
  },
  "CB2_1.jpg": {
    "timestamp": "00:16:30",
    "ocr_text": "hyphenated measures ten-rupee, five-minute, commanders-in-chief, fish, deer...",
    "type": "board"
  },
  "CB3_1.jpg": {
    "timestamp": "00:38:30",
    "ocr_text": "fractions agreement milk vs books, inanimate possessives tables legs...",
    "type": "board"
  },
  "CB4_1.jpg": {
    "timestamp": "00:45:00",
    "ocr_text": "abstract nouns generic cleanliness vs special freedom, poet and politician double articles...",
    "type": "board"
  },
  "CB5_1.jpg": {
    "timestamp": "00:58:30",
    "ocr_text": "work vs works, force vs forces, essential goods, joint Changu and Mangu possessives...",
    "type": "board"
  }
}

slide_manifest = []

with open("concept_block_map.json", "w", encoding="utf-8") as f:
    json.dump(concept_blocks, f, indent=2)

with open("frame_manifest.json", "w", encoding="utf-8") as f:
    json.dump(frame_manifest, f, indent=2)

with open("slide_manifest.json", "w", encoding="utf-8") as f:
    json.dump(slide_manifest, f, indent=2)

print("Lecture 6 Manifests generated successfully.")
