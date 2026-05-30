import json
import os

concept_blocks = [
  {
    "block_id": "CB1",
    "title": "Introduction to Transmission Media & Taxonomy (Guided vs Unguided)",
    "transcript_range_percent": [0, 15],
    "explanation": "Transmission Media represents the physical path over which data is transmitted in computer networks. The Physical Layer of the OSI model converts data bits into electromagnetic signals and sends them across the transmission medium. Transmission media is broadly categorized into two types: Guided Media (Wired) and Unguided Media (Wireless). Guided media utilizes physical cables to direct signal propagation along a specific path, directly connecting the sender and receiver. Examples include Twisted-Pair Cables, Coaxial Cables, and Fiber-Optic Cables. Unguided media transmits electromagnetic signals through free space without physical cabling, making it a wireless medium. Examples include Radio waves, Microwaves, and Infrared waves.",
    "examples": [
      {
        "sentence": "If the physical layer converts upper-layer bits into electromagnetic signals, why do we classify transmission media as either guided or unguided?",
        "rule": "Guided media physically directs signals through solid conductors (cables), while unguided media broadcasts signals through free space (wireless).",
        "working": "Electromagnetic signal propagation -> guided (uses physical copper or glass boundaries) -> unguided (uses isotropic wireless space)."
      }
    ],
    "exercise_questions": [1],
    "visual_moments": [
      {
        "timestamp": "00:01:15",
        "type": "slide",
        "slide_number": 1,
        "description": "General transmission media taxonomy slide showing Guided (twisted-pair, coaxial, fiber-optic) and Unguided (free space)."
      },
      {
        "timestamp": "00:01:25",
        "type": "board",
        "description": "Board diagram detailing physical layer signal conversion and Guided vs Unguided medium properties."
      }
    ],
    "teacher_quotes": [
      "physical layer की one of the main responsibility क्या है? कि data को... convert करके receiver पे भेजना। अब यार भेजने के लिए कोई ना कोई medium को use किया जाता है।"
    ],
    "traps": [
      "Do not confuse transmission media with the physical layer itself. Media is the physical path (cable or free space) carrying the signals, while the physical layer manages the signaling, encoding, and hardware interfaces."
    ],
    "tricks": [
      "Guided = Wired (directed path), Unguided = Wireless (free space propagation)."
    ]
  },
  {
    "block_id": "CB2",
    "title": "Guided Media: Twisted-Pair Cables (UTP vs STP) & RJ45 Connectors",
    "transcript_range_percent": [15, 50],
    "explanation": "Twisted-Pair Cable consists of two copper conductors insulated with plastic or rubber that are twisted together. Twisting is crucial because it helps cancel out electromagnetic interference and crosstalk from adjacent pairs. Twisted-pair cables are divided into Unshielded Twisted Pair (UTP), which relies strictly on outer plastic jacketing, and Shielded Twisted Pair (STP), which adds an extra metal foil shielding layer around each pair or the entire cable bundle. STP provides significantly superior noise immunity but is more expensive and bulkier. Standard telephone lines and LAN networks (e.g., 10BASE-T and 100BASE-T) utilize UTP cables, which support data rates up to 600 Mbps (CAT 7). Connectors used for twisted-pair cabling are RJ45 (Registered Jack 45) connectors, featuring 8-pin male/female jacks.",
    "examples": [
      {
        "sentence": "A network engineer needs to install cabling in an industrial factory with extreme electromagnetic noise. Which cable and connector type should be selected?",
        "rule": "STP (Shielded Twisted Pair) must be selected for high-noise environments because of its metallic foil shielding, using standard RJ45 connectors.",
        "working": "High EMI environment -> select shielded twisted pair (STP) to eliminate crosstalk -> terminate with 8-pin RJ45 registered jacks."
      }
    ],
    "exercise_questions": [2],
    "visual_moments": [
      {
        "timestamp": "00:02:30",
        "type": "slide",
        "slide_number": 2,
        "description": "Twisted-pair cable construction slide contrasting UTP (unshielded) and STP (shielded with extra metal shield)."
      },
      {
        "timestamp": "00:03:15",
        "type": "board",
        "description": "Hand-drawn board schematic showing copper conductors and how twisting cancels out external electromagnetic noise."
      },
      {
        "timestamp": "00:04:00",
        "type": "slide",
        "slide_number": 3,
        "description": "Table 7.1 displaying standard Categories of UTP cables (CAT 1 to SSTP CAT 7) with bandwidths, data rates, and common LAN usages."
      },
      {
        "timestamp": "00:05:15",
        "type": "slide",
        "slide_number": 4,
        "description": "UTP connectors drawing showing RJ-45 8-pin Male plug and Female jack configurations."
      }
    ],
    "teacher_quotes": [
      "unshielded twisted pair की तो telephone lines में, LANs में, 10BASE-T, 100BASE-T उनमें जो है वो ये use की जाती है।"
    ],
    "traps": [
      "Never use UTP in environments with high electromagnetic interference without metal conduit; always select STP for electrical noise protection."
    ],
    "tricks": [
      "RJ = Registered Jack. RJ45 has 8 pins for LANs; telephone lines traditionally used RJ11 with 4 pins."
    ]
  },
  {
    "block_id": "CB3",
    "title": "Guided Media: Coaxial Cables Construction & BNC Connectors",
    "transcript_range_percent": [50, 63],
    "explanation": "Coaxial Cable consists of an innermost single solid copper conductor surrounded by a primary insulating layer, a braided outer metal conductor/shield, and a final protective plastic cover. This multi-layered structure gives coaxial cables much higher bandwidth and better noise immunity compared to twisted-pair cables. However, high-frequency signals suffer higher attenuation, necessitating the placement of repeaters at regular intervals for long-distance lines. Coaxial cables are categorized by RG (Radio Guide) standards, including RG-59 (Cable TV), RG-58 (Thin Ethernet), and RG-11 (Thick Ethernet). They are terminated using BNC (Bayonet Neill-Concelman) connectors, including standard BNC male connectors, BNC T-connectors (for bus topology taps), and 50-ohm BNC terminators (to prevent signal reflection).",
    "examples": [
      {
        "sentence": "If thin coaxial cable (RG-58) is used in a bus topology network, what BNC components are required to connect devices and secure the signal?",
        "rule": "Coaxial networks use BNC connectors for cables, BNC T-connectors to tap into the bus, and BNC terminators to absorb signals at the open ends.",
        "working": "Coaxial RG-58 bus -> BNC connectors on cable ends -> BNC T-connectors at each NIC -> 50-ohm BNC terminators at both physical ends of the cable bus."
      }
    ],
    "examples_2": [
      {
        "sentence": "Why does coaxial cable suffer higher signal attenuation at long distances compared to other media?",
        "rule": "Coaxial cable exhibits higher attenuation at high frequencies, requiring repeaters to boost signal strength.",
        "working": "High frequency skin effect -> increases resistance -> higher signal attenuation -> install active repeaters."
      }
    ],
    "exercise_questions": [3],
    "visual_moments": [
      {
        "timestamp": "00:06:00",
        "type": "slide",
        "slide_number": 5,
        "description": "Coaxial cable layers schematic showing innermost conductor, insulator, braided outer shield, and plastic jacket."
      },
      {
        "timestamp": "00:06:20",
        "type": "board",
        "description": "Board diagram of Thin vs Thick Ethernet bus routing and active repeater placement."
      },
      {
        "timestamp": "00:07:05",
        "type": "slide",
        "slide_number": 6,
        "description": "BNC connector types slide illustrating BNC connector, BNC T-junction, and BNC 50-ohm terminator."
      }
    ],
    "teacher_quotes": [
      "Coaxial cable में BNC connector use करते हैं। BNC stands for Bayonet Neill-Concelman."
    ],
    "traps": [
      "Always ensure BNC terminators are installed at open bus cable ends. Without a terminator, the signal reflects back, causing destructive interference (ghosting)."
    ],
    "tricks": [
      "Remember: Coaxial = Cable TV (RG-59) + BNC (Bayonet Neill-Concelman)."
    ]
  },
  {
    "block_id": "CB4",
    "title": "Guided Media: Optical Fiber Cable (OFC) Structure & Connectors",
    "transcript_range_percent": [63, 85],
    "explanation": "Optical Fiber Cable (OFC) transmits data as light pulses through glass or silica fiber core rather than electrical currents over copper. Signal transmission utilizes the optical principle of Total Internal Reflection (TIR). OFC consists of a highly dense glass core surrounded by a lower-density glass cladding. Because the core has a higher refractive index than the cladding, light waves hitting the interface at angles greater than the critical angle are reflected back into the core, propagating down the line. Due to glass fragility, the core is wrapped in a plastic buffer, followed by a strength member comprised of Dupont Kevlar strands (high-tensile material used in bulletproof jackets), and covered in a thick outer PVC or Teflon jacket. OFC is a unidirectional medium requiring double channels for full-duplex communication. Connectors include SC (Subscriber Channel), ST (Straight Tip), and MT-RJ (Mechanical Transfer Registered Jack).",
    "examples": [
      {
        "sentence": "How does the density difference between the core and cladding in an optical fiber enable data transmission?",
        "rule": "The glass core is designed with a higher density than the cladding to create refractive index differential, forcing total internal reflection of light.",
        "working": "Dense core (glass) + less dense cladding (glass) -> refractive index core > cladding -> angle > critical angle -> Total Internal Reflection (TIR)."
      }
    ],
    "exercise_questions": [4],
    "visual_moments": [
      {
        "timestamp": "00:07:45",
        "type": "slide",
        "slide_number": 7,
        "description": "Optical fiber transmission slide showcasing core, cladding, critical angle reflection, and unidirectional light propagation."
      },
      {
        "timestamp": "00:07:50",
        "type": "board",
        "description": "Board drawing explaining total internal reflection (TIR) geometry and core/cladding density difference."
      },
      {
        "timestamp": "00:09:00",
        "type": "slide",
        "slide_number": 10,
        "description": "Optical fiber structural layers slide displaying Du Pont Kevlar strands, plastic buffer, glass core, cladding, and SC, ST, MT-RJ connectors."
      },
      {
        "timestamp": "00:09:10",
        "type": "board",
        "description": "Dupont Kevlar strand properties and bidirectional transmission using dual-channel layout."
      }
    ],
    "teacher_quotes": [
      "core is made up of glass. Cladding is also glass, dense core, less dense cladding... Kevlar strand is used for strength. Bulletproof jackets are also made from this Pont Kevlar."
    ],
    "traps": [
      "Do not touch or bend optical fiber cables sharply. Glass core strands are extremely thin and brittle; bending them beyond their minimum bend radius will fracture the glass and break the link."
    ],
    "tricks": [
      "Total Internal Reflection (TIR) requires: 1. Core density > Cladding density. 2. Angle of incidence > Critical angle."
    ]
  },
  {
    "block_id": "CB5",
    "title": "Optical Fiber Propagation Modes: Multimode vs Single Mode",
    "transcript_range_percent": [85, 100],
    "explanation": "Light propagates through optical fibers in two primary modes: Multimode and Single Mode. In Multimode, the glass core is thick enough to allow multiple light beams from an LED/Laser source to bounce down the core simultaneously. Multimode is further divided into Step Index and Graded Index. In Step Index Multimode, the core density is completely uniform from center to boundary. Light rays reflect at steep angles, causing significant distortion and signal dispersion. In Graded Index Multimode, the core density varies, being densest at the center and decreasing outwards. This causes light beams to travel in smooth, curved paths, significantly reducing signal distortion (highly popular for moderate distances). In Single Mode, the glass core is extremely thin (approx. 9 microns), forcing a single highly focused laser beam to propagate straight down the line without reflections. Single mode exhibits near-zero distortion and is the standard for long-haul networks.",
    "examples": [
      {
        "sentence": "If a telecommunication company needs to lay a trans-oceanic fiber link spanning thousands of kilometers, which propagation mode must be deployed and why?",
        "rule": "Single mode fiber must be deployed for ultra-long distances because its extremely thin core eliminates reflection dispersion, maximizing range and speed.",
        "working": "Trans-oceanic distance -> select Single Mode fiber -> thin glass core -> single straight laser path -> zero reflection distortion -> maximum signal fidelity."
      }
    ],
    "exercise_questions": [5],
    "visual_moments": [
      {
        "timestamp": "00:09:55",
        "type": "slide",
        "slide_number": 8,
        "description": "Propagation modes taxonomy slide dividing fiber transmission into Multimode (Step-index, Graded-index) and Single-mode."
      },
      {
        "timestamp": "00:10:45",
        "type": "slide",
        "slide_number": 9,
        "description": "Figure 7.13 showcasing Step-index (steep rays), Graded-index (curved parabolic rays), and Single-mode (straight ray) propagation wave paths."
      },
      {
        "timestamp": "00:10:50",
        "type": "board",
        "description": "Board drawing analyzing core density gradients and signal distortion difference between Step and Graded multimode propagation."
      }
    ],
    "teacher_quotes": [
      "multimode graded index is very popular because density varies and angle of reflection is curved, so less distortion."
    ],
    "traps": [
      "Never choose Step-Index Multimode for high-speed, long-distance lines. The uniform core density creates severe chromatic and modal dispersion, destroying the signal over distance."
    ],
    "tricks": [
      "Step Index = Uniform core density (steep reflections, high distortion). Graded Index = Graduated core density (curved paths, low distortion). Single Mode = Very thin core (straight path, near-zero distortion)."
    ]
  }
]

frame_manifest = {
  "CB1_1.jpg": {
    "timestamp": "00:01:25",
    "ocr_text": "GUIDED MEDIA vs UNGUIDED MEDIA: Wired (twisted pair, coaxial, fiber) vs Wireless (microwave, radio, infrared)",
    "type": "board"
  },
  "CB2_1.jpg": {
    "timestamp": "00:03:15",
    "ocr_text": "TWISTED PAIR CABLE: Two copper conductors, UTP vs STP, registered jack RJ45",
    "type": "board"
  },
  "CB3_1.jpg": {
    "timestamp": "00:05:15",
    "ocr_text": "RJ45 CONNECTORS: Registered Jack 8 pins Male and Female connectors",
    "type": "board"
  },
  "CB4_1.jpg": {
    "timestamp": "00:06:20",
    "ocr_text": "COAXIAL CABLE LAYERS: innermost copper, insulation, braided shield, outer jacket",
    "type": "board"
  },
  "CB5_1.jpg": {
    "timestamp": "00:07:50",
    "ocr_text": "TOTAL INTERNAL REFLECTION: core dense glass, cladding lower density glass",
    "type": "board"
  },
  "CB6_1.jpg": {
    "timestamp": "00:09:10",
    "ocr_text": "DUPONT KEVLAR STRANDS: Kevlar strength member for fragile glass core shielding",
    "type": "board"
  },
  "CB7_1.jpg": {
    "timestamp": "00:10:50",
    "ocr_text": "PROPAGATION MODES: Multimode step vs graded and Single mode laser straight path",
    "type": "board"
  }
}

slide_manifest = [
  {
    "slide_number": 1,
    "image_path": "slides/slide_001.png",
    "ocr_text": "Sender Physical layer Guided (twisted-pair, coaxial, fiber) Unguided (free space) Receiver Physical layer",
    "discussed_at": "00:01:15",
    "discussed": True
  },
  {
    "slide_number": 2,
    "image_path": "slides/slide_002.png",
    "ocr_text": "Twisted-pair cable: UTP (unshielded) and STP (shielded with extra metal shield)",
    "discussed_at": "00:02:30",
    "discussed": True
  },
  {
    "slide_number": 3,
    "image_path": "slides/slide_003.png",
    "ocr_text": "Table 7.1 Categories of unshielded twisted-pair cables CAT 1 to CAT 7",
    "discussed_at": "00:04:00",
    "discussed": True
  },
  {
    "slide_number": 4,
    "image_path": "slides/slide_004.png",
    "ocr_text": "Figure 7.5 UTP connector RJ-45 Male plug and Female jack",
    "discussed_at": "00:05:15",
    "discussed": True
  },
  {
    "slide_number": 5,
    "image_path": "slides/slide_005.png",
    "ocr_text": "Figure 7.7 Coaxial cable layers",
    "discussed_at": "00:06:00",
    "discussed": True
  },
  {
    "slide_number": 6,
    "image_path": "slides/slide_006.png",
    "ocr_text": "Figure 7.8 BNC connectors: Cable connector, BNC T, BNC 50-ohm terminator",
    "discussed_at": "00:07:05",
    "discussed": True
  },
  {
    "slide_number": 7,
    "image_path": "slides/slide_007.png",
    "ocr_text": "Optical fiber Core and Cladding critical angle reflection",
    "discussed_at": "00:07:45",
    "discussed": True
  },
  {
    "slide_number": 8,
    "image_path": "slides/slide_008.png",
    "ocr_text": "Figure 7.12 Propagation modes: Graded index and Single mode",
    "discussed_at": "00:09:55",
    "discussed": True
  },
  {
    "slide_number": 9,
    "image_path": "slides/slide_009.png",
    "ocr_text": "Figure 7.13 Modes: Step index ray steep path, Graded curved parabolic path, Single mode straight laser",
    "discussed_at": "00:10:45",
    "discussed": True
  },
  {
    "slide_number": 10,
    "image_path": "slides/slide_010.png",
    "ocr_text": "Du Pont Kevlar strands plastic buffer core and cladding SC, ST, MT-RJ connectors",
    "discussed_at": "00:09:00",
    "discussed": True
  }
]

with open("concept_block_map.json", "w", encoding="utf-8") as f:
    json.dump(concept_blocks, f, indent=2)

with open("frame_manifest.json", "w", encoding="utf-8") as f:
    json.dump(frame_manifest, f, indent=2)

with open("slide_manifest.json", "w", encoding="utf-8") as f:
    json.dump(slide_manifest, f, indent=2)

print("Lecture 4 Manifests generated successfully.")
