import json
import os

concept_blocks = [
  {
    "block_id": "CB1",
    "title": "Noun Practice Test: Subject-Verb Agreement & Uncountable Nouns",
    "transcript_range_percent": [0, 20],
    "explanation": "This section discusses key rules of subject-verb agreement and noun categorization using standard exam questions from Noun Practice Test 01. First, singular diseases or conditions ending in 's' (e.g., Measles, Mumps, Rickets, AIDS, Psoriasis) are singular nouns and must be paired with singular verbs (e.g., 'Measles is...'). Second, in the 'One of + Plural Noun' structure, the noun following 'one of' must always be plural (e.g., 'one of those diseases'). However, when followed by a relative pronoun like 'that', the subsequent verb agrees with the plural antecedent (e.g., 'diseases that weaken...'). Third, collective values or quantities like 'twenty million degrees' represent a unified single temperature or sum and take singular verbs (e.g., 'twenty million degrees is enough'). Finally, uncountable nouns such as 'advice' cannot be paired with indefinite articles like 'a/an' (use 'advice' or 'a piece of advice', never 'an advice').",
    "examples": [
      {
        "sentence": "Measles is one of those diseases that weaken a person's immunity.",
        "rule": "Singular diseases ending in 's' are singular; 'One of' must be followed by a plural noun; relative clauses agree with the plural antecedent.",
        "working": "Measles (singular disease) -> is (singular verb) -> one of those diseases (plural noun) -> that weaken (agrees with plural diseases)."
      },
      {
        "sentence": "Twenty million degrees at the core of the sun is enough to melt anything and everything.",
        "rule": "Quantities of temperature, distance, or money represent a single collective unit and take singular verbs.",
        "working": "Twenty million degrees -> represents a single temperature -> takes singular verb 'is enough'."
      },
      {
        "sentence": "When Katie decided to adopt a child, her mother gave her advice.",
        "rule": "Uncountable nouns like 'advice' cannot take indefinite articles like 'a/an'.",
        "working": "an advice -> incorrect -> replace with 'advice' or 'a piece of advice'."
      }
    ],
    "exercise_questions": [1, 2, 3],
    "visual_moments": [
      {
        "timestamp": "00:04:15",
        "type": "board",
        "description": "Measles, mumps, rickets, AIDS rules and one of + plural noun subject-verb agreement on the board."
      }
    ],
    "teacher_quotes": [
      "पहला point तो यह होगा कि आपका जो यह measles है... diseases which end in 'es' but actually they are always singulars.",
      "जहां one of लिखा हुआ है ना, उसके पीछे हर हालत में plural noun आएगा। 100% आएगा।"
    ],
    "traps": [
      "Never write 'an advice' or 'a measles'; uncountable nouns and singular diseases must be treated correctly."
    ],
    "tricks": [
      "Remember: Singular disease = singular verb. One of = plural noun."
    ]
  },
  {
    "block_id": "CB2",
    "title": "Primary Purpose of Place Nouns & Pronoun Case Selection",
    "transcript_range_percent": [20, 40],
    "explanation": "This block covers rules regarding definite articles with place nouns and choosing pronoun cases in compound structures. Place nouns like school, church, college, temple, hospital, and prison omit the definite article 'the' when they are visited for their primary, institutional purpose (e.g., 'goes to church every Sunday' to pray). The definite article 'the' is only used when referring to a specific, physical building for a secondary purpose (e.g., 'the church he goes to is located near the library'). Additionally, in compound subjects, pronouns must be in the subjective case rather than the objective case (e.g., 'Raju and I argued' instead of 'Raju and me argued'). Test this by isolating the pronoun (you would say 'I argued', never 'me argued').",
    "examples": [
      {
        "sentence": "Jimmy goes to church every Sunday and the church he goes to is located near the library.",
        "rule": "Omit 'the' before primary places when visited for their primary purpose; use 'the' when referring to a specific building/location.",
        "working": "goes to the church -> primary purpose (worship) -> change to 'goes to church' -> the church he goes to -> specific church -> correct."
      },
      {
        "sentence": "Raju and I argued about the role of creative writing in modern history.",
        "rule": "Use subjective case pronouns (I, he, she, they) in subject positions, even when paired with a proper noun in a compound subject.",
        "working": "Raju and me -> subject position -> isolate pronoun: 'me argued' is incorrect -> change to subjective case: 'Raju and I argued'."
      }
    ],
    "exercise_questions": [4, 5],
    "visual_moments": [
      {
        "timestamp": "00:15:40",
        "type": "board",
        "description": "Primary vs secondary purpose of place nouns article rules and subjective/objective pronoun case tables on the board."
      }
    ],
    "teacher_quotes": [
      "जब आप कोई भी article नहीं use कर रहे, बिल्कुल उसके बिना आप noun use कर रहे... goes to church आएगा।",
      "Raju and me argued... me eats बोलते हैं या I eat बोलते हैं? Subjective case I होना चाहिए।"
    ],
    "traps": [
      "Do not use 'the' for routine school/church visits; do not use objective pronouns like 'me' or 'myself' as subjects."
    ],
    "tricks": [
      "To test compound subjects, remove the proper noun: 'Raju and [me/I] argued' -> '[I] argued' is correct."
    ]
  },
  {
    "block_id": "CB3",
    "title": "Pronoun Ordering Rules & Collective Nouns Agreement",
    "transcript_range_percent": [40, 73],
    "explanation": "This section addresses two common grammar concepts: ordering multiple personal pronouns and handling collective nouns that are divided. First, when writing multiple personal pronouns in a positive or neutral sentence, they must be arranged in the 2-3-1 order: Second Person (you), Third Person (he, she, they, proper names), and First Person (I, we). For example, 'You, Ravi and I will represent our college.' Second, time/duration expressions use the form 'years of experience' or the genitive 'years' experience' (e.g., 'ten years of experience'). Third, collective nouns like 'team', 'jury', or 'committee' take plural pronouns and verbs when there is disagreement or division among the members (e.g., 'The team couldn't win because they were split into two factions'). Finally, subject-verb agreement requires matching the verb to the plural head noun in phrases like 'questions are enough', not the singular infinitive phrase.",
    "examples": [
      {
        "sentence": "You, Ravi and I will represent our college in the contest.",
        "rule": "Arrange multiple personal pronouns in the 2-3-1 order (Second, Third, First) for normal positive statements.",
        "working": "I, you and Ravi -> incorrect order -> apply 2-3-1: You (2nd) -> Ravi (3rd) -> I (1st) -> 'You, Ravi and I'."
      },
      {
        "sentence": "We are looking for someone having a good knowledge of French and ten years of experience.",
        "rule": "Use plural measure nouns followed by 'of' or possessive apostrophe for duration expressions.",
        "working": "ten year experience -> incorrect -> change to 'ten years of experience' or 'ten years' experience'."
      },
      {
        "sentence": "The team couldn't win because they were split into two factions.",
        "rule": "Collective nouns take plural pronouns and verbs when their members are acting individually or are divided.",
        "working": "team -> split into factions -> members are divided -> use plural pronoun 'they were split'."
      }
    ],
    "exercise_questions": [6, 7, 8],
    "visual_moments": [
      {
        "timestamp": "00:51:10",
        "type": "board",
        "description": "2-3-1 pronoun order diagram and collective noun singular vs plural division guidelines."
      }
    ],
    "teacher_quotes": [
      "जब भी आप arrange करते हैं, एक से ऊपर pronoun अगर है... यह typical order होता है pronoun को लिखने का: 2-3-1।",
      "The team couldn't win because they were split into two factions."
    ],
    "traps": [
      "Never use 1-2-3 order for positive sentences; collective nouns are only singular when acting as a single unified body."
    ],
    "tricks": [
      "2-3-1 for positive/neutral sentences. 1-2-3 is only used for admitting mistakes, guilt, or negative sentences."
    ]
  },
  {
    "block_id": "CB4",
    "title": "Indefinite Articles Generic Use & Unspecified Reference",
    "transcript_range_percent": [73, 83],
    "explanation": "This block introduces the basic usage of indefinite articles 'a' and 'an' for unspecified singular countable nouns. An indefinite article is used when a noun is mentioned for the first time and its identity is unknown or unspecified to the listener (e.g., 'A thief came to my house last night', 'A man was killed in an accident'). Furthermore, 'a/an' can be used generically to represent any member of a class or group as a representative example (e.g., 'A surgeon needs to be very careful' meaning all surgeons, 'A dog is a faithful animal' representing all dogs). This is also highlighted in famous quotations where a generic idea is introduced, such as: 'Nothing is as powerful as an idea whose time has come.'",
    "examples": [
      {
        "sentence": "A thief came to my house last night.",
        "rule": "Use indefinite articles for singular countable nouns whose identity is unspecified or new to the discourse.",
        "working": "unspecified thief -> singular count noun -> prefix with 'A'."
      },
      {
        "sentence": "A surgeon needs to be very careful.",
        "rule": "Use indefinite articles generically to denote a whole class or group represented by any single member.",
        "working": "surgeon (any representative surgeon) -> 'A surgeon' meaning 'all surgeons'."
      },
      {
        "sentence": "Nothing is as powerful as an idea whose time has come.",
        "rule": "Generic abstract concepts use 'an' to represent any single abstract unit.",
        "working": "idea (starts with vowel sound) -> 'an idea'."
      }
    ],
    "exercise_questions": [9, 10],
    "visual_moments": [
      {
        "timestamp": "01:00:06",
        "type": "board",
        "description": "Rules of generic indefinite article class representation with thief and surgeon examples."
      }
    ],
    "teacher_quotes": [
      "A surgeon needs to be very careful... meaning all surgeons... A dog is a faithful animal.",
      "Nothing is as powerful as an idea whose time has come."
    ],
    "traps": [
      "Do not use definite articles for completely new, unspecified singular entities; do not omit the article for singular countable nouns."
    ],
    "tricks": [
      "Generic class: 'A surgeon...' = 'Every surgeon...'"
    ]
  },
  {
    "block_id": "CB5",
    "title": "Sound-Based 'A' vs 'An' & Silent Letters / Consonant Sounds",
    "transcript_range_percent": [83, 100],
    "explanation": "This section explains the core phonetic rules of indefinite article selection. Choosing between 'a' and 'an' depends entirely on the initial sound of the following word, not its spelling. First, 'an' is used before silent 'H' words (e.g., 'an honest girl', 'an hour', 'an historical building', 'an historic occasion'). Second, 'an' is used before abbreviations that begin with consonant letters but produce initial vowel sounds (e.g., 'an M.Phil.', 'an M.A.', 'an M.Sc.', 'an M.Com.', 'an MD' -> sound starts with 'E'). Conversely, 'a' is used before abbreviations starting with consonant sounds (e.g., 'a PhD', 'a BA'). Third, 'a' is used before words starting with vowel letters that produce consonant sounds: 'Y' sound (e.g., 'a university', 'a European') or 'W' sound (e.g., 'a one-eyed man'). Finally, a noun takes 'a/an' on first mention and 'the' on subsequent mention (e.g., 'We had a good picnic yesterday. The picnic was...').",
    "examples": [
      {
        "sentence": "She is an M.Phil. student and he is a PhD holder.",
        "rule": "Use 'an' for abbreviations starting with vowel sounds (e.g., M.Phil. starts with 'E') and 'a' for consonant sounds (e.g., PhD starts with 'P').",
        "working": "M.Phil. -> pronounced 'em-phil' -> initial sound 'E' (vowel) -> 'an M.Phil.' | PhD -> pronounced 'pee-aitch-dee' -> initial 'P' (consonant) -> 'a PhD'."
      },
      {
        "sentence": "I met a university professor and a European tourist.",
        "rule": "Use 'a' before words starting with vowel letters that produce initial consonant 'Y' sounds.",
        "working": "university -> pronounced 'yoo-ni-versity' -> initial sound 'Y' (consonant) -> 'a university' | European -> pronounced 'yoo-ropean' -> initial sound 'Y' -> 'a European'."
      },
      {
        "sentence": "They came across a one-eyed man.",
        "rule": "Use 'a' before words starting with vowel letters that produce initial consonant 'W' sounds.",
        "working": "one -> pronounced 'wan' -> initial sound 'W' (consonant) -> 'a one-eyed man'."
      },
      {
        "sentence": "We had a good picnic yesterday. The picnic was great.",
        "rule": "Use 'a/an' for the first mention of an entity, and 'the' for subsequent mentions when it becomes specified.",
        "working": "first mention -> 'a good picnic' -> second mention -> 'The picnic'."
      }
    ],
    "exercise_questions": [11, 12, 13],
    "visual_moments": [
      {
        "timestamp": "01:10:45",
        "type": "board",
        "description": "Phonetic sounds chart showing vowel vs consonant initial sounds and silent letter exception lists."
      }
    ],
    "teacher_quotes": [
      "कहानी सारी sound की है... university में शुरू में U लगा है but sound is coming from Y.",
      "BA की sound B से sound शुरू हो रही है... an बिल्कुल नहीं आएगा।",
      "We had a good picnic yesterday. Stop. ... then the picnic बोल सकते हैं।"
    ],
    "traps": [
      "Do not write 'an university' or 'a M.A.'; always evaluate by sound rather than written spelling."
    ],
    "tricks": [
      "Write out the pronunciation in your native language or phonetically: 'M.A.' starts with 'E' ('em'), so it takes 'an'. 'University' starts with 'Y' ('yoo'), so it takes 'a'."
    ]
  }
]

frame_manifest = {
  "CB1_1.jpg": {
    "timestamp": "00:04:15",
    "ocr_text": "Measles is one of those diseases that weaken...",
    "type": "board"
  },
  "CB2_1.jpg": {
    "timestamp": "00:15:40",
    "ocr_text": "goes to church, Raju and I argued...",
    "type": "board"
  },
  "CB3_1.jpg": {
    "timestamp": "00:51:10",
    "ocr_text": "pronouns 2-3-1 order, team were split...",
    "type": "board"
  },
  "CB4_1.jpg": {
    "timestamp": "01:00:06",
    "ocr_text": "A surgeon, thief came, generic a/an...",
    "type": "board"
  },
  "CB5_1.jpg": {
    "timestamp": "01:10:45",
    "ocr_text": "an M.Phil., a university, sound based rules...",
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

print("Lecture 5 Manifests generated successfully.")
