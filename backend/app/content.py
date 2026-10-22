"""Curriculum and review-ready study cards for the local content service.

These are concise revision cards, not a replacement for licensed question-bank
or textbook content. The API keeps the chapter taxonomy complete and makes
the most useful formula/reaction/NCERT anchors searchable.
"""

from __future__ import annotations

from typing import Any


Subject = str
ClassLevel = str

CURRICULUM: dict[str, dict[Subject, list[str]]] = {
    "11th": {
        "Physics": ["Physical World", "Units and Measurements", "Motion in a Straight Line", "Motion in a Plane", "Laws of Motion", "Work, Energy and Power", "System of Particles and Rotational Motion", "Gravitation", "Mechanical Properties of Solids", "Mechanical Properties of Fluids", "Thermal Properties of Matter", "Thermodynamics", "Kinetic Theory", "Oscillations", "Waves"],
        "Chemistry": ["Some Basic Concepts of Chemistry", "Structure of Atom", "Classification of Elements and Periodicity", "Chemical Bonding and Molecular Structure", "Thermodynamics", "Equilibrium", "Redox Reactions", "Organic Chemistry: Basic Principles", "Hydrocarbons", "The s-Block Elements", "Some p-Block Elements", "Environmental Chemistry"],
        "Biology": ["The Living World", "Biological Classification", "Plant Kingdom", "Animal Kingdom", "Morphology of Flowering Plants", "Anatomy of Flowering Plants", "Structural Organisation in Animals", "Cell: The Unit of Life", "Biomolecules", "Cell Cycle and Cell Division", "Transport in Plants", "Mineral Nutrition", "Photosynthesis in Plants", "Respiration in Plants", "Plant Growth and Development", "Digestion and Absorption", "Breathing and Exchange of Gases", "Body Fluids and Circulation", "Excretory Products and Elimination", "Locomotion and Movement", "Neural Control and Coordination", "Chemical Coordination and Integration"],
    },
    "12th": {
        "Physics": ["Electric Charges and Fields", "Electrostatic Potential and Capacitance", "Current Electricity", "Moving Charges and Magnetism", "Magnetism and Matter", "Electromagnetic Induction", "Alternating Current", "Electromagnetic Waves", "Ray Optics and Optical Instruments", "Wave Optics", "Dual Nature of Radiation and Matter", "Atoms", "Nuclei", "Semiconductor Electronics"],
        "Chemistry": ["Solutions", "Electrochemistry", "Chemical Kinetics", "d and f Block Elements", "Coordination Compounds", "Haloalkanes and Haloarenes", "Alcohols, Phenols and Ethers", "Aldehydes, Ketones and Carboxylic Acids", "Amines", "Biomolecules", "Polymers", "Chemistry in Everyday Life", "Surface Chemistry", "General Principles and Processes of Isolation of Elements", "p-Block Elements"],
        "Biology": ["Reproduction in Organisms", "Sexual Reproduction in Flowering Plants", "Human Reproduction", "Reproductive Health", "Principles of Inheritance and Variation", "Molecular Basis of Inheritance", "Evolution", "Human Health and Disease", "Strategies for Enhancement in Food Production", "Microbes in Human Welfare", "Biotechnology: Principles and Processes", "Biotechnology and its Applications", "Organisms and Populations", "Ecosystem", "Biodiversity and Conservation", "Environmental Issues"],
    },
}


CARDS: dict[tuple[Subject, str], list[tuple[str, str, str]]] = {
    ("Physics", "Motion in a Straight Line"): [("Key formula", "v = u + at · s = ut + ½at² · v² = u² + 2as", "Check sign convention before substitution."), ("Graph recall", "Slope of x–t graph = velocity · slope of v–t graph = acceleration", "Use area under v–t graph for displacement.")],
    ("Physics", "Laws of Motion"): [("Key formula", "F = ma · impulse J = Δp · fₘₐₓ = μₛN", "Draw the free-body diagram first."), ("Exam anchor", "Action and reaction act on different bodies", "Do not cancel them on one free-body diagram.")],
    ("Physics", "Work, Energy and Power"): [("Key formula", "W = Fs cos θ · K = ½mv² · P = W/t", "For variable force, work is area under F–x graph."), ("Conservation", "Kᵢ + Uᵢ = K𝒇 + U𝒇 when only conservative forces act", "Track the chosen zero of potential energy.")],
    ("Physics", "Electric Charges and Fields"): [("Key formula", "F = kq₁q₂/r² · E = F/q · Φ = EA cos θ", "Field is a vector; potential is a scalar."), ("Gauss law", "∮E·dA = qᵢₙ/ε₀", "Choose a Gaussian surface only when symmetry supports it.")],
    ("Physics", "Current Electricity"): [("Key formula", "V = IR · R = ρL/A · P = VI", "Series current is common; parallel voltage is common."), ("Network recall", "Kirchhoff junction rule: ΣI = 0", "Assign a loop direction and keep signs consistent.")],
    ("Physics", "Ray Optics and Optical Instruments"): [("Lens formula", "1/f = 1/v − 1/u · m = v/u", "Use Cartesian sign convention for every distance."), ("Refraction", "n₁ sin i = n₂ sin r", "Total internal reflection needs denser-to-rarer travel and i > c.")],
    ("Physics", "Dual Nature of Radiation and Matter"): [("Key formula", "E = hν · λ = h/p · Kₘₐₓ = hν − φ", "Stopping potential satisfies eV₀ = Kₘₐₓ."), ("Photoelectric anchor", "Intensity changes photocurrent; frequency changes maximum kinetic energy", "Threshold frequency is material-dependent.")],
    ("Chemistry", "Some Basic Concepts of Chemistry"): [("Mole map", "n = m/M · M = moles/V(L) · χᵢ = nᵢ/Σn", "Identify the limiting reagent before calculating yield."), ("Yield", "% yield = actual yield/theoretical yield × 100", "Keep units consistent throughout the calculation.")],
    ("Chemistry", "Chemical Bonding and Molecular Structure"): [("Formal charge", "FC = valence e⁻ − non-bonding e⁻ − ½(bonding e⁻)", "The most stable Lewis structure minimises charge separation."), ("Magnetism", "μ = √(n(n + 2)) BM", "Count unpaired electrons, not total electrons.")],
    ("Chemistry", "Equilibrium"): [("Equilibrium", "Kp = Kc(RT)^Δn · pH = −log[H⁺]", "Pure solids and liquids are omitted from K expressions."), ("Buffer", "pH = pKa + log(salt/acid)", "Use concentrations or moles in the same ratio.")],
    ("Chemistry", "Electrochemistry"): [("Cell potential", "E°cell = E°cathode − E°anode · ΔG° = −nFE°cell", "Spontaneous galvanic cells have positive E°cell."), ("Conductance", "κ = Gl/A · Λm = κ × 1000/C", "Check concentration units before using molar conductivity.")],
    ("Chemistry", "Chemical Kinetics"): [("Rate law", "rate = k[A]ᵐ[B]ⁿ · order = m + n", "Overall order is the sum of experimentally found powers."), ("First order", "t₁/₂ = 0.693/k", "First-order half-life is independent of initial concentration.")],
    ("Chemistry", "Aldehydes, Ketones and Carboxylic Acids"): [("Aldol", "2CH₃CHO → CH₃CH(OH)CH₂CHO → CH₃CH=CHCHO + H₂O", "An α-hydrogen and suitable base are required."), ("Oxidation", "RCHO + [O] → RCOOH", "Aldehydes oxidise more readily than ketones.")],
    ("Chemistry", "Amines"): [("Hofmann rearrangement", "RCONH₂ + Br₂ + 4KOH → RNH₂ + 2KBr + K₂CO₃ + 2H₂O", "The product has one carbon fewer than the amide."), ("Diazotisation", "ArNH₂ + NaNO₂ + HCl (0–5°C) → ArN₂⁺Cl⁻", "Temperature control is essential for diazonium salt formation.")],
    ("Biology", "Cell: The Unit of Life"): [("NCERT recall", "Plasma membrane is selectively permeable; mitochondria and chloroplasts are semi-autonomous.", "Compare prokaryotic and eukaryotic cell organisation."), ("Diagram anchor", "Ribosomes synthesise proteins; lysosomes contain hydrolytic enzymes.", "Label organelles with one structure and one function.")],
    ("Biology", "Photosynthesis in Plants"): [("Pathway", "Light reaction forms ATP and NADPH; Calvin cycle uses them to fix CO₂.", "Separate thylakoid events from stroma events."), ("NCERT anchor", "Cyclic photophosphorylation involves PSI; non-cyclic flow involves PSI and PSII.", "Remember the role of the reaction centre pigments.")],
    ("Biology", "Human Reproduction"): [("Sequence", "Spermatogenesis → fertilisation → cleavage → implantation → gastrulation.", "Place events on a timeline before revising hormones."), ("Hormone anchor", "FSH supports follicular growth; LH surge triggers ovulation.", "Link each hormone to its source and target.")],
    ("Biology", "Molecular Basis of Inheritance"): [("Central dogma", "DNA replication → transcription → translation", "Replication is semiconservative and DNA polymerase extends 5′→3′."), ("Operon recall", "The lac operon is inducible and regulated by a repressor plus an inducer.", "Distinguish regulatory gene, promoter, operator and structural genes.")],
    ("Biology", "Human Health and Disease"): [("Immunity", "Innate immunity is non-specific; acquired immunity is specific and develops memory.", "Compare active versus passive immunity by source, speed and memory."), ("Disease recall", "Vaccination primes a primary response so a later exposure can produce a stronger secondary response.", "Revise pathogen, transmission and prevention together.")],
    ("Biology", "Ecosystem"): [("Energy flow", "Energy transfer is unidirectional; only a fraction passes to the next trophic level.", "Differentiate standing crop, productivity and decomposition."), ("Cycle anchor", "Decomposers return nutrients to the ecosystem while energy is lost as heat.", "Draw one carbon or nitrogen cycle from memory.")],
}


def _default_cards(subject: Subject, chapter: str) -> list[tuple[str, str, str]]:
    if subject == "Physics":
        content = f"{chapter}: define the quantities, write the governing relation and check SI units before solving."
        return [("Chapter anchor", content, "Add a worked example after revising the definition."), ("Revision prompt", f"What is the graph, limiting case or sign convention for {chapter}?", "Answer from memory, then verify against your approved text.")]
    if subject == "Chemistry":
        return [("Reaction map", f"{chapter}: reactant → reagent/condition → product; annotate oxidation state or mechanism where relevant.", "Write conditions above the arrow."), ("Concept prompt", f"Which exception or trend is most tested in {chapter}?", "Compare the rule with one known exception.")]
    return [("NCERT anchor", f"{chapter}: revise the definition, labelled diagram, sequence and one exception.", "Use active recall before rereading."), ("Application prompt", f"Where does {chapter} connect to human health, ecology or biotechnology?", "Answer in two precise sentences.")]


def _expanded_cards(subject: Subject, chapter: str) -> list[tuple[str, str, str]]:
    """Return a useful minimum content set for every chapter.

    The curated CARDS above are kept as the primary source for high-yield
    chapters.  These additional cards make the complete syllabus browsable and
    give each chapter the same revision workflow until a licensed content
    import replaces the starter copy.
    """
    primary = CARDS.get((subject, chapter), _default_cards(subject, chapter))
    if subject == "Physics":
        extras = [
            ("Concept map", f"{chapter}: identify the physical quantities, their dimensions, direction/sign convention and limiting case.", "Write the known quantities before selecting a governing equation."),
            ("Common trap", f"For {chapter}, check units, graph meaning and boundary conditions before trusting a numerical answer.", "A correct formula with an incorrect sign or unit still gives a wrong answer."),
            ("Active recall", f"Close your notes and explain {chapter} in three lines: definition, governing relation and one application.", "Then solve one basic and one mixed-concept question."),
        ]
    elif subject == "Chemistry":
        extras = [
            ("Concept map", f"{chapter}: connect the definition, governing equation, units, trend or reaction mechanism before memorising exceptions.", "Write reagents and conditions above every reaction arrow."),
            ("Common trap", f"In {chapter}, check state symbols, sign convention, limiting reagent, catalyst and temperature wherever applicable.", "Separate what changes the rate from what changes the equilibrium or product."),
            ("Active recall", f"Close your notes and recall the key trend, equation and one named reaction from {chapter}.", "Verify the product, condition and exception against your approved material."),
        ]
    else:
        extras = [
            ("NCERT map", f"{chapter}: revise the definition, sequence, labelled structure, function and one NCERT exception.", "Link every fact to a diagram, process or comparison table."),
            ("Common trap", f"For {chapter}, distinguish similar terms, stages, structures and examples before attempting assertion questions.", "Look for absolute words such as always, only and never."),
            ("Active recall", f"Explain {chapter} from memory in five points, then draw or label the most important process.", "Finish with three NCERT line-based questions."),
        ]
    return primary + extras


def question_bank(class_level: ClassLevel = "Mixed", subject: Subject = "Mixed", difficulty: str = "Mixed") -> list[dict[str, Any]]:
    """Build a chapter-linked practice bank covering the full PCB taxonomy.

    Curated seed questions are followed by two short mastery checks per
    chapter.  The latter are deliberately labelled as chapter checks: they
    provide complete navigation and revision coverage without pretending to be
    imported PYQs.  Approved question imports can replace or extend them.
    """
    selected_subjects = ["Physics", "Chemistry", "Biology"] if subject in {"Mixed", "All"} else [subject]
    entries: list[dict[str, Any]] = []
    for chapter_info in chapters(class_level, "All"):
        item_subject = chapter_info["subject"]
        if item_subject not in selected_subjects:
            continue
        chapter = chapter_info["chapter"]
        cards = _expanded_cards(item_subject, chapter)
        anchor = cards[0]
        recall = cards[1]
        chapter_key = f"{chapter_info['class_level']}-{item_subject}-{chapter}"
        generated = [
            {
                "id": f"check-{chapter_key}-01",
                "class_level": chapter_info["class_level"],
                "subject": item_subject,
                "chapter": chapter,
                "topic": "Chapter mastery",
                "difficulty": "Easy",
                "type": "chapter_check",
                "text": f"Which revision approach best fits {chapter}?",
                "options": [
                    f"Start with the definition, governing idea and one application",
                    "Memorise isolated answers without checking the concept",
                    "Skip units, diagrams and conditions",
                    "Revise only the chapter title",
                ],
                "answer": 0,
                "explanation": anchor[1],
            },
            {
                "id": f"check-{chapter_key}-02",
                "class_level": chapter_info["class_level"],
                "subject": item_subject,
                "chapter": chapter,
                "topic": "Exam habits",
                "difficulty": "Medium",
                "type": "chapter_check",
                "text": f"What should a student verify before finalising an answer from {chapter}?",
                "options": [
                    "Only the option length",
                    recall[2],
                    "Whether the question uses a familiar font",
                    "Nothing; the first guess is enough",
                ],
                "answer": 1,
                "explanation": recall[1],
            },
        ]
        if difficulty != "Mixed":
            generated = [item for item in generated if item["difficulty"] == difficulty]
        entries.extend(generated)
    return entries


def chapters(class_level: ClassLevel = "Mixed", subject: Subject = "All") -> list[dict[str, str]]:
    levels = ["11th", "12th"] if class_level == "Mixed" else [class_level]
    subjects = ["Physics", "Chemistry", "Biology"] if subject == "All" else [subject]
    return [{"class_level": level, "subject": item, "chapter": chapter} for level in levels for item in subjects for chapter in CURRICULUM[level][item]]


def references(class_level: ClassLevel = "Mixed", subject: Subject = "All", query: str = "") -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    needle = query.strip().lower()
    for chapter_info in chapters(class_level, subject):
        item_subject = chapter_info["subject"]
        chapter = chapter_info["chapter"]
        cards = _expanded_cards(item_subject, chapter)
        for index, (kind, content, note) in enumerate(cards):
            entry = {
                "id": f"{chapter_info['class_level']}-{item_subject}-{chapter}-{index}",
                "classLevel": chapter_info["class_level"],
                "subject": item_subject,
                "chapter": chapter,
                "title": f"{chapter} · {kind}",
                "kind": kind,
                "content": content,
                "note": note,
                "revisionMinutes": 8 if index < 2 else 5,
                "sourceLabel": "PrePora starter reference",
            }
            haystack = f"{entry['title']} {entry['content']} {entry['note']}".lower()
            if not needle or needle in haystack:
                entries.append(entry)
    return entries
