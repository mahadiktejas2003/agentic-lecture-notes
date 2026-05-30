import json
import os

concept_blocks = [
  {
    "block_id": "CB1",
    "title": "Noun Practice Test Discussion (Questions 1 to 5)",
    "transcript_range_percent": [0, 24],
    "explanation": "This block covers the first five questions of the Noun Practice Test, detailing critical subject-verb agreement (SVA), uncountable noun properties, and article rules. First, disease names ending in 's' (e.g., measles, mumps, rickets, AIDS, psoriasis) represent a single disease entity and are grammatically singular, requiring a singular verb (e.g., 'Measles is...'). Second, the phrase 'one of' must always be followed by a plural noun (e.g., 'one of those diseases'). In relative clauses following 'one of [plural noun] that/which', standard grammar often uses a plural verb, but the specific teacher rule dictates that the relative pronoun refers back to the singular 'one' (preceding the preposition 'of'), thus taking a singular verb (e.g., 'weakens', not 'weaken'). Third, expressions denoting temperature, sums of money, or distances (e.g., 'twenty million degrees', 'five hundred rupees') represent a single unified quantity/concept and agree with a singular verb (e.g., 'is enough', 'is a big sum'), as they stand for 'A temperature of twenty million degrees'. Fourth, 'advice' is strictly an uncountable noun; it can never be preceded by 'an' or pluralized as 'advices' (except in commercial notifications). Instead, use 'a piece of advice' or 'a word of advice'. 'Advise' is strictly a verb. Fifth, when two subjects are connected by 'with', 'together with', 'along with', 'as well as', or 'besides', the verb must agree with the first subject (e.g., 'his star with thousands of his fans campaigned/campaigns'). Sixth, routine or habitual visits to institutional places (e.g., church, school, office, temple) for their primary purpose (e.g., worship, study, work, prayer) omit articles (e.g., 'goes to church'). However, when referring to a specific building/site or for secondary purposes, a definite article is required (e.g., 'the church he goes to').",
    "examples": [
      {
        "sentence": "Measles is one of those diseases that weakens a person's immunity.",
        "rule": "Disease names are singular; 'one of' takes a plural noun; the relative clause verb agrees with singular 'one'.",
        "working": "Measles -> is (singular disease) | one of those disease -> incorrect -> change to 'one of those diseases' | that weaken -> teacher-specified relative agreement -> change to 'that weakens'."
      },
      {
        "sentence": "Twenty million degrees at the core of the sun is enough to melt anything and everything.",
        "rule": "Expressions of temperature, distance, or sums are treated as a singular unified quantity.",
        "working": "twenty million degrees... are enough -> represents a single temperature -> change 'are' to 'is'."
      },
      {
        "sentence": "When Katie decided to adopt a child, her mother gave her a piece of advice.",
        "rule": "'Advice' is an uncountable noun (noun case); do not write 'an advice' or 'advices'. 'Advise' is the verb form.",
        "working": "gave her an advice -> uncountable -> change to 'gave her a piece of advice' or 'gave her advice'."
      },
      {
        "sentence": "During elections his star with thousands of his fans campaigns for the ruling party.",
        "rule": "Subjects joined by 'with', 'together with', 'along with', 'as well as', 'besides' agree with the first subject.",
        "working": "star (singular) with fans (plural) -> campaign -> first subject is singular -> change to 'campaigns' or 'campaigned'."
      },
      {
        "sentence": "Jimmy goes to church every Sunday and the church he goes to is located near the library.",
        "rule": "Omit articles for routine visits to places for their primary purpose; use 'the' for specific building references.",
        "working": "goes to the church -> primary purpose (worship) -> omit 'the' -> 'goes to church' | the church he goes to -> specific building -> correct."
      }
    ],
    "exercise_questions": [1, 2, 3, 4, 5],
    "visual_moments": [
      {
        "timestamp": "00:04:30",
        "type": "board",
        "description": "Analysis of Practice Test Q1-Q5, listing singular diseases (measles, mumps) and the primary purpose article omission rule."
      }
    ],
    "teacher_quotes": [
      "Measles is... Disease name is always a singular. One of के पीछे हर हालत में plural noun आएगा... One out of many ही हो सकता है।",
      "preposition जो पहली है वो of है तो of के पहले one है, one singular है, one के साथ weakens आएगा, weaken नहीं आएगा।",
      "Five hundred rupees is a big sum... the subject is a temperature of twenty million degrees, which is singular.",
      "Goes to church means routine activity, no article needed. But the church he goes to represents a specific building, so the is required."
    ],
    "traps": [
      "Never use 'an advice' or 'advices' for general recommendations; do not pluralize primary purpose institutions in routine actions."
    ],
    "tricks": [
      "Preposition rule: Look at the noun *before* the first preposition to find the true subject (e.g., 'one' in 'one of those...')."
    ]
  },
  {
    "block_id": "CB2",
    "title": "Noun Practice Test Discussion (Questions 6 to 11)",
    "transcript_range_percent": [24, 46],
    "explanation": "This block covers questions six through eleven, discussing subjective active pronouns, consistency in indefinite subjects, possessive forms, and emphatic constructions. First, active sentences must use subjective case pronouns ('I', 'we', 'he', 'she') for subjects performing actions, rather than objective case ('me', 'us', 'him', 'her') or reflexive pronouns (e.g., 'Raju and I' instead of 'Raju and me'). Never start active sentences with 'me' or 'myself' for introductions; write 'I am [Name]'. Second, if a sentence begins with 'one' as an indefinite pronoun meaning everyone/anyone, subsequent pronoun references to that person must also be 'one' or 'one's', not 'he' or 'she' (e.g., 'If one accepts... one is going'). Third, in contractions, 'it's' stands for 'it is', whereas 'its' is the possessive pronoun (e.g., 'its legs', 'its milk'). When writing active sentences referring to a country or noun, do not omit the subject pronoun (e.g., 'now it is being rebuilt' or 'now it's being rebuilt'). Fourth, 'each' is grammatically singular and requires a singular verb in present tense third person (e.g., 'each of their songs reminds', not 'remind'). The word 'hymn' translates to a chant or shlok. Fifth, emphatic sentences starting with 'It is/was' are followed by the subjective pronoun case (e.g., 'It was we who had documented...', not 'It was us who'). Check this by dropping the emphatic frame: 'We had documented...' is grammatically correct. Sixth, emphatic introductory structures use 'It is/was...', not 'That is/was...' (e.g., 'It is humility which sets apart...').",
    "examples": [
      {
        "sentence": "Raju and I argued about the role of creative writing in modern history.",
        "rule": "Active voice subjects must use the subjective pronoun case (I, we, he, she), not objective (me, us) or reflexive.",
        "working": "Raju and me argued -> 'me' is objective -> change to subjective -> 'Raju and I argued'."
      },
      {
        "sentence": "If one accepts the reality of life, one is going to lead a peaceful life.",
        "rule": "Subsequent pronoun references to the indefinite subject 'one' must remain 'one' or 'one's' for consistency.",
        "working": "If one accepts... he is going -> change 'he' to 'one' to maintain subject agreement."
      },
      {
        "sentence": "Iraq was destroyed by the American army and now it is being rebuilt by the American companies which caused its destruction.",
        "rule": "Do not omit the subject pronoun/verb ('it is' / 'it's') before passive verbs; distinguish between 'it's' (it is) and 'its' (possessive).",
        "working": "and now is being rebuilt -> add subject and auxiliary -> change to 'now it is being rebuilt' or 'now it's being rebuilt'."
      },
      {
        "sentence": "Every part of Mongolian life is infused with music and each of their songs reminds them of their ancient hymns.",
        "rule": "'Each' is singular and requires a singular verb ('reminds') in present tense third person; 'hymn' means chant/shlok.",
        "working": "each of their songs remind -> 'each' is singular -> change 'remind' to 'reminds'."
      },
      {
        "sentence": "It was we who had documented the Naxalite movement among the tribals.",
        "rule": "Emphatic 'It was/is' frames must be followed by subjective pronouns (we, I, he, she), not objective ones (us, me, him, her).",
        "working": "It was us who -> incorrect -> change 'us' to 'we' | test: 'We had documented the movement' is correct."
      },
      {
        "sentence": "It is humility which sets apart the truly great men from others.",
        "rule": "Emphatic introductory constructions utilize the pronoun 'It' rather than 'That'.",
        "working": "That is humility which sets -> change 'That' to 'It'."
      }
    ],
    "exercise_questions": [6, 7, 8, 9, 10, 11],
    "visual_moments": [
      {
        "timestamp": "00:19:00",
        "type": "board",
        "description": "Chart explaining subjective vs objective pronouns (I vs me), 'one' consistency, and emphatic 'It was we' rules."
      }
    ],
    "teacher_quotes": [
      "Never start a sentence with me, him, her, us. When you do the action, it must be active voice: Raju and I argued.",
      "Calling yourself 'myself Devajit' is the worst kind of introduction. Please say 'I am Devajit Chaudhary'.",
      "If one accepts... behind one, only one should come, not he or she.",
      "Its without apostrophe is possessive (its legs are broken). It's with apostrophe is it is. Here it must be 'now it is being rebuilt'.",
      "Each is singular, so it must be reminds, not remind.",
      "It was we who... Check it by removing 'It was/who': We had documented... So we is subjective and correct."
    ],
    "traps": [
      "Avoid introducing yourself with 'Myself' or starting active subject roles with 'me'. Do not confuse the contraction 'it's' with possessive 'its'."
    ],
    "tricks": [
      "Emphatic Check: Drop the 'It was [pronoun] who' frame from the sentence; the correct pronoun will naturally align with the remaining verb (e.g., 'We had documented' -> 'It was we who had documented')."
    ]
  },
  {
    "block_id": "CB3",
    "title": "Noun Practice Test Discussion (Questions 12 to 17)",
    "transcript_range_percent": [46, 68],
    "explanation": "This block covers questions twelve through seventeen, analyzing uncountable nouns, SVA with collective nouns, separate possessives, geographical articles, and negative sentence phrasing. First, 'bread' is strictly uncountable; the plural form 'breads' does not exist in standard English. To indicate quantity, use countable classifiers such as 'slices of bread', 'pieces of bread', or 'loaves of bread'. Similar uncountable nouns include mischief (acts of mischief), information (pieces of information), furniture (articles of furniture), news (items of news), and kindness (acts of kindness). Second, a collective noun representing a single unified group (e.g., 'a band of robbers') acts as a singular subject and takes a singular verb (e.g., 'has entered', not 'have entered'), because the true subject is 'band', not 'robbers' (which must be plural because a group requires multiple people). Third, when two nouns connect by 'and', giving separate possessive apostrophes to both indicates separate ownership or separate actions (e.g., 'both India's and China's poets' or adjective form 'both Indian and Chinese poets'), as they wrote distinct poems rather than a joint one. Fourth, mountain ranges (e.g., the Nilgiris, the Himalayas, the Alps, the Andes) always require the definite article 'the'. 'Sanatorium' denotes a medical facility for patients recuperating from long-term illnesses like TB. Fifth, to express a negative idea for a group, standard style prefers negative quantifiers like 'none' or 'neither' rather than 'each... not' or 'both... not'. Use 'None of us likes the movie' (with singular verb 'likes' agreeing with 'none') instead of 'Each of us do not like', and 'Neither of them is intelligent' (with singular verb 'is') instead of 'Both of them are not'.",
    "examples": [
      {
        "sentence": "As the boy was very hungry, he ate two slices of bread.",
        "rule": "'Bread' is uncountable; use classifiers like 'slices', 'pieces', or 'loaves' instead of plural 'breads'.",
        "working": "he ate two breads -> uncountable -> change to 'two slices of bread' or 'two loaves of bread'."
      },
      {
        "sentence": "A band of robbers has entered the village.",
        "rule": "Collective group subjects ('a band') are singular; 'robbers' must remain plural as a group requires multiple members.",
        "working": "A band of robbers have entered -> the subject is singular 'band' -> change 'have' to 'has'."
      },
      {
        "sentence": "Both Indian and Chinese poets have glorified the beauty of the Himalayas.",
        "rule": "Separate actions or separate entities require separate possessives ('both India's and China's') or adjectives ('both Indian and Chinese').",
        "working": "Both India and China poets -> separate entities -> change to 'both Indian and Chinese' or 'both India's and China's'."
      },
      {
        "sentence": "Sullivan discovered the Nilgiris and was the first one to see their potential as a sanatorium.",
        "rule": "Mountain ranges require the definite article 'the'; 'sanatorium' is a recovery place for recuperating TB patients.",
        "working": "discovered Nilgiris -> mountain range -> change to 'discovered the Nilgiris'."
      },
      {
        "sentence": "None of us likes the movie.",
        "rule": "Prefer negative quantifiers ('none of us') over 'each of us do not'; 'none' takes a singular verb ('likes') in standard usage.",
        "working": "Each of us do not like the movie -> negative sense -> change to 'None of us likes the movie'."
      },
      {
        "sentence": "Neither of them is intelligent.",
        "rule": "Prefer 'neither of them' (which is singular and takes a singular verb 'is') over negative both constructions ('both of them are not').",
        "working": "Both of them are not intelligent -> negative comparison -> change to 'Neither of them is intelligent'."
      }
    ],
    "exercise_questions": [12, 13, 14, 15, 16, 17],
    "visual_moments": [
      {
        "timestamp": "00:27:00",
        "type": "board",
        "description": "Examples showing uncountable nouns (bread vs slices), collective noun SVA (band has), mountain articles, and 'neither/none' negative structures."
      }
    ],
    "teacher_quotes": [
      "Breads name ka noun hota hi nahi hai. Pieces of bread, slices of bread, or loaves of bread. Mischiefs nahi hota, acts of mischief hota hai.",
      "A band of robbers has entered. Robin is singular, but a group cannot have one member. Robbers is correct, but the verb agrees with singular band.",
      "Separate possessives: Indias and Chinas, because they wrote separate poems. If joint, we put apostrophe S only on the last name.",
      "Mountains, rivers name always take the: The Nilgiris, The Satpuras, The Alps. Sanatorium is midway recovery home for TB patients.",
      "Both of them are not intelligent is bad style. Negative comparison use neither: Neither of them is intelligent. Cut the 'not'."
    ],
    "traps": [
      "Never use 'breads' or 'mischiefs'; do not use plural verbs for collective group subjects like 'band' or negative subjects like 'neither'."
    ],
    "tricks": [
      "Negative Formulation Trick: When correcting a sentence containing a negative 'each... not' or 'both... not', substitute 'none' or 'neither' respectively, and convert the verb to singular while removing 'not'."
    ]
  },
  {
    "block_id": "CB4",
    "title": "Noun Practice Test Discussion (Questions 18 to 23)",
    "transcript_range_percent": [68, 83],
    "explanation": "This block covers questions eighteen through twenty-three, focusing on 'one of' reinforcement, specific body organs, police collective SVA, closest subject agreement, and comparative structures. First, 'one of my favorite books' is correct because 'one of' is followed by a plural noun. The relative clause verb 'I read' is correct because 'I' takes a plural verb form. Second, a singular country possessive is singular (e.g., 'Pakistan's new government') and matches a singular verb (e.g., 'faces'). Third, specific anatomical organs and systems of the body require the definite article 'the' (e.g., 'sent to the brain', not 'sent to brain'). A mismatch can be written as 'a mismatch' or 'some mismatch'. Fourth, the collective noun 'police' in Indian and British English is strictly treated as plural and requires plural verbs and pronouns (e.g., 'The police believe they are...'). Fifth, when two subjects are connected by 'neither... nor', 'either... or', or 'not only... but also', the verb must agree in number with the *nearest* subject (e.g., 'Neither the leader nor the members have been told', where 'members' is plural and nearest, requiring 'have'). Sixth, in comparisons, avoid comparing a noun to a pronoun of a different category (illogical comparison). Compare similar items (e.g., 'His car is bigger than mine' instead of 'bigger than me', where 'mine' means 'my car' and prevents repetition).",
    "examples": [
      {
        "sentence": "This is one of my favorite books which I read very often.",
        "rule": "'One of' takes plural nouns; 'I' takes standard plural verb form; the sentence is correct.",
        "working": "favorite book -> incorrect -> must be 'favorite books' | which I read -> correct."
      },
      {
        "sentence": "Pakistan's new government faces a threat as is clear from the Pakistani President's statement.",
        "rule": "A singular country possessive represents a singular entity and agrees with a singular verb.",
        "working": "government faces -> singular subject -> correct."
      },
      {
        "sentence": "Dizziness occurs when there is a mismatch in the information sent to the brain.",
        "rule": "Define specific anatomical organs with the definite article 'the'; ensure indefinite modifiers for mismatch.",
        "working": "information sent to brain -> specific organ -> change to 'sent to the brain'."
      },
      {
        "sentence": "The police believe they are very close to catching the criminal.",
        "rule": "'Police' is strictly plural in Indian/British English; follow 'close to' with a gerund (ing form), not an infinitive.",
        "working": "The police believes -> incorrect -> change to 'believe' | close to catch -> infinitive incorrect -> change to 'close to catching' (gerund like 'addicted to gambling')."
      },
      {
        "sentence": "Neither the leader nor the members have been told about the decision.",
        "rule": "In 'neither... nor' SVA, the verb agrees with the nearest subject ('members' -> plural -> 'have').",
        "working": "members has been -> nearest subject is plural -> change 'has' to 'have'."
      },
      {
        "sentence": "His car is bigger than mine and I know it quite well.",
        "rule": "Ensure logical comparisons between equivalent items; use possessive pronouns ('mine' -> my car) to avoid repetition.",
        "working": "bigger than me -> comparing car to a person -> change to 'bigger than mine' or 'bigger than my car'."
      }
    ],
    "exercise_questions": [18, 19, 20, 21, 22, 23],
    "visual_moments": [
      {
        "timestamp": "00:36:30",
        "type": "board",
        "description": "Rules for body organs (the brain), plural police SVA, nearest subject rules for neither/nor SVA, and logical comparison models."
      }
    ],
    "teacher_quotes": [
      "One of my favorite books... plural noun is mandatory. I read is correct because I takes plural verb form.",
      "Pakistan's new government faces... government is singular, faces is singular. Correct.",
      "mismatch in the information sent to the brain. Brain is organ, the is required.",
      "Police in Indian and British English is always plural. Believes is wrong, it must be believe. They are close to catching. Gerund will come.",
      "Close to catching... addicted to gambling, close to reaching. Remember the ing form.",
      "Neither nor nearest subject agrees. Leader is singular, members is plural. Has closest to members is wrong, it must be have.",
      "His car is bigger than me is illogical. Comparison must be between car and car. Change me to mine (meaning my car)."
    ],
    "traps": [
      "Do not treat 'police' as singular; do not use infinitive 'to catch' after 'close to'; avoid illogical comparisons comparing objects to people."
    ],
    "tricks": [
      "Nearest Subject Trick: In 'neither/nor' sentences, physically cover everything before 'nor' and read the remaining subject with the verb to check agreement (e.g., 'the members [have] been told')."
    ]
  },
  {
    "block_id": "CB5",
    "title": "Noun Practice Test Discussion (Questions 24 to 29)",
    "transcript_range_percent": [83, 100],
    "explanation": "This block covers questions twenty-four through twenty-nine, detailing comparisons with famous figures, uncountable qualities, fixed alert phrasing, SVA with split collective nouns, time quantifiers, and pronoun ordering. First, when comparing a person to a famous figure to bestow their exceptional qualities, place the definite article 'the' before the famous figure's name (e.g., 'touted as the Amitabh Bachchan of the television world', 'the Shakespeare of India'). 'Touted' means publicized or promoted. Second, 'success' is an uncountable noun; omit the indefinite article 'a' (e.g., 'got success' or 'got much success' or 'achieved success'). Second-class citizen discrimination in South Africa was called Apartheid, which ended in 1993 under Nelson Mandela. Third, the public is treated as a singular collective subject ('has been told'), but the fixed idiomatic prepositional phrase requires an article (e.g., 'on the alert' or 'on a high alert'). Fourth, when a collective noun (e.g., 'the team') is split, divided, or shows disagreement, it acts as a plural subject requiring plural verbs and pronouns (e.g., 'they were split into two factions'). Fifth, time measure plurals inside an 'of' construction do not use an apostrophe (e.g., 'ten years of experience' spelled y-e-a-r-s). Sixth, when combining multiple pronouns in positive or neutral contexts, they must be arranged in the 2-3-1 order (Second person 'You', Third person 'Ravi'/names, First person 'I').",
    "examples": [
      {
        "sentence": "Once upon a time Kamal Preet was touted as the Amitabh Bachchan of the television world.",
        "rule": "Use 'the' before a proper noun when comparing a person's qualities to a famous figure.",
        "working": "touted as Amitabh Bachchan -> quality comparison -> change to 'touted as the Amitabh Bachchan'."
      },
      {
        "sentence": "Martin Luther King and Gandhi struggled against racial discrimination and got success.",
        "rule": "'Success' is uncountable; do not use 'a lot of' with 'a' article or 'a success' (use 'success' or 'much success').",
        "working": "got a lot of success -> uncountable -> change to 'got success' or 'got much success' or 'achieved success'."
      },
      {
        "sentence": "The public has been told to be on the alert after the recent terrorist attack.",
        "rule": "'Public' acts as a singular collective; the fixed prepositional idiom is 'on the alert' or 'on a high alert'.",
        "working": "to be on alert -> fixed idiom -> change to 'to be on the alert' or 'to be on a high alert'."
      },
      {
        "sentence": "The team couldn't win because they were split into two factions.",
        "rule": "A collective noun is treated as plural when its members are divided in opinion or split; use 'factions' for division.",
        "working": "because it was split into two halves -> team members divided -> change 'it was' to 'they were' | 'two halves' -> 'two factions'."
      },
      {
        "sentence": "We are looking for someone having a good knowledge of French and ten years of experience.",
        "rule": "Do not insert an apostrophe in plural time units preceding 'of' constructions; spell y-e-a-r-s.",
        "working": "ten years of experience -> spelling y-e-a-r-s -> correct."
      },
      {
        "sentence": "You, Ravi and I will represent our college in the contest.",
        "rule": "Arrange multiple pronouns in positive/neutral contexts in the 2-3-1 order (Second, Third, First person).",
        "working": "I, you and Ravi -> incorrect ordering -> change to 'You, Ravi and I'."
      }
    ],
    "exercise_questions": [24, 25, 26, 27, 28, 29],
    "visual_moments": [
      {
        "timestamp": "00:47:15",
        "type": "board",
        "description": "Formulas for proper noun comparisons, success uncountability, divided collective noun plurals, and the 2-3-1 pronoun order."
      }
    ],
    "teacher_quotes": [
      "Comparison with famous figure takes the: The Amitabh Bachchan, The Shakespeare. Touted means promote/publicity.",
      "Success is uncountable, got a lot of success is wrong, omit a. Got success or achieved success.",
      "Racial discrimination is Apartheid. South Africa policy ended in 1993, Nelson Mandela jail for 27 years.",
      "Public has been told is singular, but idiom is on the alert or on a high alert. Add the.",
      "Team couldn't win because they were split. Division makes collective noun plural. Split into two factions.",
      "Ten years of experience. y-e-a-r-s, no apostrophe, no tricks.",
      "Pronoun order is 2-3-1: Second person (You), Third person (Ravi/names), First person (I). You, Ravi and I is correct."
    ],
    "traps": [
      "Do not use apostrophes in time quantifiers like 'ten years of experience'; do not use singular pronouns for divided collective nouns."
    ],
    "tricks": [
      "Pronoun Ordering Code: Remember '2-3-1' (You, He/Name, I) for standard/polite sentences, putting yourself last."
    ]
  },
  {
    "block_id": "CB6",
    "title": "Core Grammar - Articles (A vs An)",
    "transcript_range_percent": [55, 100],
    "explanation": "This block introduces the core rules governing indefinite articles 'A' vs 'An'. First, the choice between 'A' and 'An' is strictly determined by *vowel sounds*, not vowel letters! Standard vowel letters are A, E, I, O, U, but they must produce vowel sounds to take 'An'. Basic vowel sound examples include 'an ant colony', 'an elephantine memory' (excellent memory), 'an ink pot', 'an owl', and 'an ugly fight'. Second, words beginning with a silent 'H' where the sound begins with a vowel require 'An' (e.g., 'an honest girl', 'an hotel', 'an hour', 'an historical building/novel', 'an historic occasion'). Third, abbreviations starting with letters that possess vowel sounds (specifically F, H, L, M, N, R, S, X, which are pronounced as 'ef', 'aitch', 'el', 'em', 'en', 'ar', 'es', 'ex') take 'An' (e.g., 'an M.Phil. in economics', 'an M.A. degree', 'an MSc', 'an M.Com.', 'an MD degree', 'an FIR', 'an SDM'). In contrast, abbreviations starting with consonant sounds take 'A' (e.g., 'a B.A. degree', 'a PhD', 'a B.Sc.'). Fourth, words beginning with vowel letters that produce consonant sounds take 'A' (e.g., 'a university professor' producing a 'Y'/'yoo' sound, 'a European' producing a 'Y'/'yoo' sound, 'a one-eyed man' or 'a one-rupee note' producing a 'V'/'wan' sound). Fifth, 'A' has three major semantic usages: (1) **One**: meaning 'single entity' (e.g., 'wait for a minute', 'make a call', 'had a good picnic yesterday'); (2) **Uncertainty**: representing an unknown entity to the speaker (e.g., 'a thief struck at my house last night' meaning 'some unknown thief', 'a man was killed'); (3) **Group Representation (Class/Generic)**: expressing a generic standard quality for an entire group (e.g., 'a surgeon needs to be careful' meaning all surgeons, 'a dog is a faithful animal' meaning all dogs, 'a cow is sacred'). A famous generic quote is: 'Nothing is as powerful as an idea whose time has come' (Victor Hugo).",
    "examples": [
      {
        "sentence": "She has an elephantine memory and bought an ink pot.",
        "rule": "Words beginning with vowel letters producing vowel sounds take 'An'.",
        "working": "elephantine (E sound) -> an elephantine | ink pot (I sound) -> an ink pot."
      },
      {
        "sentence": "An hour passed before we could find an honest historic hotel.",
        "rule": "Words starting with a silent 'H' where the sound begins with a vowel require 'An'.",
        "working": "hour (O sound) -> an hour | honest (O sound) -> an honest | hotel (O sound) -> an hotel | historic (I sound) -> an historic."
      },
      {
        "sentence": "She holds an M.A. and an M.Phil., whereas he holds a PhD.",
        "rule": "Abbreviations starting with vowel-sound letters (M pronounced as 'em') take 'An'; consonant sounds take 'A'.",
        "working": "M.A. (em sound) -> an M.A. | M.Phil. (em sound) -> an M.Phil. | PhD (P sound) -> a PhD."
      },
      {
        "sentence": "I met a European university professor who was a one-eyed man.",
        "rule": "Words starting with vowel letters that produce consonant sounds (university/European -> 'Y' sound, one -> 'V' sound) take 'A'.",
        "working": "European ('yoo' sound) -> a European | university ('yoo' sound) -> a university | one-eyed ('wan' sound) -> a one-eyed."
      },
      {
        "sentence": "A surgeon needs to be careful, just as a dog is a faithful animal.",
        "rule": "Use 'A' for group representation to convey a generic quality applicable to all members.",
        "working": "surgeon (all surgeons) -> a surgeon | dog (all dogs) -> a dog."
      }
    ],
    "exercise_questions": [30],
    "visual_moments": [
      {
        "timestamp": "01:05:30",
        "type": "board",
        "description": "Chart mapping indefinite articles (A vs An) based on vowel sounds, silent 'H' lists, abbreviation rules, and consonant-sound vowel letters."
      }
    ],
    "teacher_quotes": [
      "Indefinite article is entirely sound based, not letter based. Elephantine memory, owl, ugly fight take an.",
      "Silent H: An honest girl, an hotel, an hour, an historical building, an historic occasion. H is silent.",
      "An M.Phil., an M.A., an MSc, an M.Com., an MD. M is pronounced as 'em', sound starts with E. But a B.A., a PhD because B and P are consonant sounds.",
      "A university, a European take a because they start with 'yoo' Y sound. A one-eyed man, a one-rupee note take a because they start with 'wan' V sound.",
      "A has three senses: One (wait a minute), Uncertainty (a thief came, some unknown thief), and Group Quality (a surgeon needs to be careful, meaning all surgeons)."
    ],
    "traps": [
      "Do not write 'an university', 'an European', or 'an one-eyed man'; do not use 'a' for abbreviations starting with vowel sounds like M.A."
    ],
    "tricks": [
      "Phonetic sound test: Pronounce the word aloud. If the first sound is a vowel (e.g. 'em' for M, 'our' for hour), use 'An'. If it is a consonant (e.g. 'yoo' for university, 'wan' for one), use 'A'."
    ]
  }
]

frame_manifest = {
  "CB1_1.jpg": {
    "timestamp": "00:04:30",
    "ocr_text": "Q1-Q5: Measles SVA, one of rules, twenty million degrees is, piece of advice, with joiners, church article omission.",
    "type": "board"
  },
  "CB2_1.jpg": {
    "timestamp": "00:19:00",
    "ocr_text": "Q6-Q11: subjective I, one consistency, it is / it's being rebuilt, each reminds, It was we who, It is humility.",
    "type": "board"
  },
  "CB3_1.jpg": {
    "timestamp": "00:27:00",
    "ocr_text": "Q12-Q17: slices of bread uncountables, band has entered, Indian and Chinese separate, the Nilgiris sanatorium, none/neither negatives.",
    "type": "board"
  },
  "CB4_1.jpg": {
    "timestamp": "00:36:30",
    "ocr_text": "Q18-Q23: favorite books, government faces, specific the brain, police believe they are, close to catching, nearest members have, bigger than mine.",
    "type": "board"
  },
  "CB5_1.jpg": {
    "timestamp": "00:47:15",
    "ocr_text": "Q24-Q29: the Amitabh Bachchan touting, success uncountables, on the alert idiom, split team they were, ten years of experience, 2-3-1 You, Ravi and I.",
    "type": "board"
  },
  "CB6_1.jpg": {
    "timestamp": "01:05:30",
    "ocr_text": "Articles: vowel sounds an ant/elephantine/owl, silent H honest/hour/hotel/historic, abbreviations an M.A./M.Phil/MSc vs a PhD/B.A., consonant U/E/O university/European/one-eyed, three senses of A.",
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

print("Lecture 7 Manifests generated successfully.")
