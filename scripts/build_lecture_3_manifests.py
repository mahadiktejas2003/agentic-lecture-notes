import json
import os

concept_blocks = [
  {
    "block_id": "CB1",
    "title": "Introduction to OSI Model & Layered Stack Architecture",
    "transcript_range_percent": [0, 23],
    "explanation": "The Open System Interconnection (OSI) model is a conceptual framework developed to standardize communications across diverse computer systems and devices connected via the Internet. The model groups all set of rules and protocols into seven distinct layers. The OSI architecture is fundamentally a stack architecture because it follows the Last-In, First-Out (LIFO) model. On the sender side, the application layer is the first to process data, and the physical layer is the last to process and encapsulate the data into signals. On the receiver side, the physical layer is the very first to receive and decode the signals, demonstrating a strict LIFO processing model. To easily remember the order of the seven layers from bottom to top, the mnemonic 'Please Do Not Throw Sausage Pizza Away' is commonly used.",
    "examples": [
      {
        "sentence": "If the sender uses 7 layers to generate and encapsulate data, and the receiver decodes it in reverse order, why is it called a Stack Architecture?",
        "rule": "Stack architecture is characterized by Last-In, First-Out (LIFO). The physical layer is the last to process data on the sender side and the first to process data on the receiver side.",
        "working": "Sender: App -> Pres -> Sess -> Trans -> Net -> DLL -> Phys (Phys is last). Receiver: Phys -> DLL -> Net -> Trans -> Sess -> Pres -> App (Phys is first) -> LIFO -> Stack Architecture."
      }
    ],
    "exercise_questions": [1],
    "visual_moments": [
      {
        "timestamp": "00:00:10",
        "type": "slide",
        "slide_number": 1,
        "description": "OSI Lecture Title Slide: OSI Layers and Their Responsibilities."
      },
      {
        "timestamp": "00:03:00",
        "type": "board",
        "description": "OSI 7-layer stack diagram showing sender-to-receiver encapsulation flow."
      }
    ],
    "teacher_quotes": [
      "OSI model की जो layers है वहाँ से इसकी कहानी जो है वो start होती है। उन layers की क्या responsibility है और computer networks का syllabus actual में OSI की 7 layers ही है।"
    ],
    "traps": [
      "Don't confuse Stack Architecture with queue processing. It is strictly LIFO."
    ],
    "tricks": [
      "To remember the 7 layers in order from bottom to top: 'Please Do Not Throw Sausage Pizza Away' (Physical, Data Link, Network, Transport, Session, Presentation, Application)."
    ]
  },
  {
    "block_id": "CB2",
    "title": "The Lower Layers: Physical Layer & Data Link Layer Responsibilities",
    "transcript_range_percent": [23, 61],
    "explanation": "The Physical Layer (Layer 1) handles the physical transmission of raw bits over electromagnetic signals across the transmission media (wired/wireless). It defines cables, topologies, encoding schemes (such as Manchester and NRZ), and operates devices like Repeaters and Hubs. The Data Link Layer (Layer 2) is responsible for host-to-host (hop-to-hop or node-to-node) delivery. It splits the incoming packets into frames (framing) and uses a 48-bit physical address known as the MAC address. It is responsible for flow control (Stop-and-Wait, Go-Back-N, and Selective Repeat), error control (CRC, Parity, and Checksum), and access control (Aloha, CSMA, and CSMA/CD). Physical devices operating at this layer include Bridges and Switches.",
    "examples": [
      {
        "sentence": "A sender transmits data over a LAN. How are flow control and access control managed at the node-to-node level?",
        "rule": "Data Link Layer manages node-to-node (hop-to-hop) delivery, physical addressing (48-bit MAC), flow control (Stop-and-Wait, GBN, SR), and access control (Aloha, CSMA/CD).",
        "working": "Data link layer encapsulates network packets into frames -> adds MAC addresses -> applies Stop-and-Wait flow control -> CSMA/CD for access control -> CRC for error detection."
      }
    ],
    "exercise_questions": [2],
    "visual_moments": [
      {
        "timestamp": "00:04:55",
        "type": "slide",
        "slide_number": 5,
        "description": "Physical Layer: Raw Bits, signals, cables, and electromagnetic conversion."
      },
      {
        "timestamp": "00:08:24",
        "type": "slide",
        "slide_number": 6,
        "description": "Data Link Layer: Framing, physical addressing, hop-to-hop routing, and flow/error control."
      },
      {
        "timestamp": "00:08:24",
        "type": "board",
        "description": "Physical layer devices (Repeater and Hub) block diagram."
      },
      {
        "timestamp": "00:11:52",
        "type": "board",
        "description": "Data Link Layer flow, error, and access control protocols listing."
      }
    ],
    "teacher_quotes": [
      "Data Link Layer की responsibility है host to host... Better इसको आप क्या लिखो hop to hop, hop to hop delivery."
    ],
    "traps": [
      "MAC address is physical (48-bit) and operates at Data Link Layer, while IP address is logical and operates at Network Layer. Never mix them up."
    ],
    "tricks": [
      "Remember: DLL = MAC, IP = Network. MAC handles local hop delivery, IP handles end-to-end routing."
    ]
  },
  {
    "block_id": "CB3",
    "title": "The Network Layer: Source-to-Destination logical Delivery & Routing",
    "transcript_range_percent": [61, 70],
    "explanation": "The Network Layer (Layer 3) is responsible for the source-to-destination (end-to-end) delivery of packets across multiple networks. It achieves this by using logical addressing (such as 32-bit IPv4 or 128-bit IPv6) instead of physical addressing. The layer determines the optimal path to transmit data using routing algorithms like Distance Vector Routing and Link State Routing. The service is fundamentally a datagram service, meaning individual packets are routed independently and may travel along entirely different paths to reach their destination. Physical devices operating at this layer include Routers and Layer 3 Switches.",
    "examples": [
      {
        "sentence": "If two packets from the same source to the same destination travel through different routers, how does the Network Layer handle it?",
        "rule": "Network Layer uses datagram service for source-to-destination packet routing. Packets travel independently and can take different paths.",
        "working": "Datagram service -> independent routing -> packets take different paths based on Distance Vector/Link State algorithms -> destination IP address is verified."
      }
    ],
    "exercise_questions": [3],
    "visual_moments": [
      {
        "timestamp": "00:13:03",
        "type": "slide",
        "slide_number": 7,
        "description": "Network Layer Slide: Logical addressing (IP), datagram services, and routing protocols."
      },
      {
        "timestamp": "00:13:30",
        "type": "board",
        "description": "Network Layer routing showing packet traversal through different paths."
      }
    ],
    "teacher_quotes": [
      "Network layer की responsibility है source to destination मतलब मेरे system से data निकल के destination पर कैसे पहुंचेगा."
    ],
    "traps": [
      "The Network Layer does not guarantee in-order delivery of packets; that is the job of the Transport Layer."
    ],
    "tricks": [
      "Logical addressing = Network Layer (IP). Routing = Network Layer."
    ]
  },
  {
    "block_id": "CB4",
    "title": "The Transport Layer: Process-to-Process Port Delivery",
    "transcript_range_percent": [70, 79],
    "explanation": "The Transport Layer (Layer 4) is responsible for process-to-process (port-to-port or end-to-end) delivery of data segments. It operates on port addresses, which are logical addresses assigned to specific running software processes by the operating system. The Transport Layer handles segment reassembly, flow control, congestion control, and error control (checksum). It defines two main protocols: Transmission Control Protocol (TCP), which is connection-oriented and utilizes a reliable three-way handshaking mechanism, and User Datagram Protocol (UDP), which is a faster but connectionless and unreliable protocol. Sequence numbers are appended to each segment to ensure correct reordering at the destination. Gateways operate at this layer.",
    "examples": [
      {
        "sentence": "How does the Transport Layer reassemble out-of-order packets received from the Network Layer?",
        "rule": "Transport Layer uses sequence numbers in segments to reorder, reassemble, and perform error/flow/congestion control.",
        "working": "Packets arrive out-of-order -> Transport Layer reads sequence numbers -> reassembles segments -> checks checksum -> connection-oriented TCP handles three-way handshake."
      }
    ],
    "exercise_questions": [4],
    "visual_moments": [
      {
        "timestamp": "00:15:01",
        "type": "slide",
        "slide_number": 8,
        "description": "Transport Layer Slide: Process-to-process delivery, TCP/UDP protocols, and sequence control."
      },
      {
        "timestamp": "00:15:30",
        "type": "board",
        "description": "Port addressing and process-to-process delivery with sequence numbers."
      }
    ],
    "teacher_quotes": [
      "Transport layer का काम क्या है? Process to process delivery। इसको हम end to end भी बोलते हैं या फिर इसको हम port to port delivery भी बोलते हैं."
    ],
    "traps": [
      "Transport Layer handles port-to-port process delivery, not host-to-host physical delivery. Port numbers are assigned by OS."
    ],
    "tricks": [
      "TCP = connection-oriented (reliable, 3-way handshake). UDP = connectionless (fast, unreliable)."
    ]
  },
  {
    "block_id": "CB5",
    "title": "The Upper Layers: Session, Presentation, and Application Layers",
    "transcript_range_percent": [79, 100],
    "explanation": "The three upper layers are primarily software-oriented. The Session Layer (Layer 5) manages dialogue control, synchronization points, and half-duplex/full-duplex communications, establishing and maintaining active sessions (such as online banking session timeouts). The Presentation Layer (Layer 6) handles translation, data formatting (such as ASCII or EBCDIC), compression, and security features like encryption and decryption. The Application Layer (Layer 7) provides user-level interfaces and integrates network processes with user software applications via protocols such as HTTP, HTTPS, FTP, SMTP, DNS, POP, and Telnet.",
    "examples": [
      {
        "sentence": "When a user logs into net banking and is automatically logged out after 5 minutes of inactivity, which layer is responsible?",
        "rule": "Session Layer manages session creation, dialogue control, and synchronization, including idle timeouts.",
        "working": "Net banking login -> Session created -> Timer monitored by Session Layer -> Inactivity for 5 mins -> Session terminated."
      },
      {
        "sentence": "How is data secured and compressed before it is sent over the network medium?",
        "rule": "Presentation Layer handles encryption, decryption, compression, and data syntax formatting (translation).",
        "working": "Pure data from Application Layer -> Encryption and compression applied by Presentation Layer -> Syntax formatted (ASCII/EBCDIC)."
      }
    ],
    "exercise_questions": [5],
    "visual_moments": [
      {
        "timestamp": "00:17:15",
        "type": "slide",
        "slide_number": 9,
        "description": "Session Layer Slide: Dialog initiation, connection persistence, and synchronization."
      },
      {
        "timestamp": "00:17:15",
        "type": "board",
        "description": "Session synchronization and banking session example."
      },
      {
        "timestamp": "00:18:22",
        "type": "slide",
        "slide_number": 10,
        "description": "Presentation Layer Slide: Data syntax conversion, encryption, decryption, and compression."
      },
      {
        "timestamp": "00:19:30",
        "type": "slide",
        "slide_number": 11,
        "description": "Application Layer Slide: User interface, network software interactions, and common services."
      },
      {
        "timestamp": "00:19:30",
        "type": "board",
        "description": "Application layer protocols (DNS, HTTP, SMTP)."
      }
    ],
    "teacher_quotes": [
      "Presentation layer name से ही point पता लग रहा है present करना है... Dialogue control और synchronization का काम है session layer का... Application layer basically क्या है user level service."
    ],
    "traps": [
      "The application layer does not contain the actual applications (like Chrome or Outlook) but the protocols (HTTP, SMTP) they use to interact with the network."
    ],
    "tricks": [
      "Remember the three upper layers as the Software/User layers. Application = interface, Presentation = translation/security, Session = management."
    ]
  }
]

frame_manifest = {
  "CB1_1.jpg": {
    "timestamp": "00:03:00",
    "ocr_text": "OSI 7 LAYER MODEL: Application, Presentation, Session, Transport, Network, Data Link, Physical",
    "type": "board"
  },
  "CB2_1.jpg": {
    "timestamp": "00:08:24",
    "ocr_text": "PHYSICAL LAYER DEVICES: REPEATER AND HUB (Layer 1)",
    "type": "board"
  },
  "CB3_1.jpg": {
    "timestamp": "00:11:52",
    "ocr_text": "DATA LINK LAYER PROTOCOLS: ETHERNET, MAC ADDRESSING, FLOW/ERROR/ACCESS CONTROL",
    "type": "board"
  },
  "CB4_1.jpg": {
    "timestamp": "00:13:30",
    "ocr_text": "NETWORK LAYER ROUTING: logical addressing, distance vector routing, link state routing",
    "type": "board"
  },
  "CB5_1.jpg": {
    "timestamp": "00:15:30",
    "ocr_text": "TRANSPORT LAYER PROCESS DELIVERY: TCP, UDP, port numbers, sequence numbers",
    "type": "board"
  },
  "CB6_1.jpg": {
    "timestamp": "00:17:15",
    "ocr_text": "SESSION LAYER SYNCHRONIZATION: dialog management, synchronization points",
    "type": "board"
  },
  "CB7_1.jpg": {
    "timestamp": "00:19:30",
    "ocr_text": "APPLICATION LAYER SERVICES: DNS, HTTP, SMTP, FTP, POP, TELNET",
    "type": "board"
  }
}

with open("concept_block_map.json", "w", encoding="utf-8") as f:
    json.dump(concept_blocks, f, indent=2)

with open("frame_manifest.json", "w", encoding="utf-8") as f:
    json.dump(frame_manifest, f, indent=2)

print("Manifests generated successfully.")
