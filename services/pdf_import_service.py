import re
import io
import spacy
import pdfplumber

def extract_cues_from_pdf(pdf_bytes: bytes):
    """
    Extrahiert Cues, Rollen und Dialoge aus einem Theater-Skript PDF.
    Gibt (full_text, cues_list, roles_list) zurück.
    """
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    import sys
    import os
    
    model_name = 'de_core_news_sm'
    
    def log_debug(msg):
        try:
            with open("debug_spacy.txt", "a") as f:
                f.write(msg + "\n")
        except:
            pass

    log_debug(f"Loading spaCy model: {model_name}")
    log_debug(f"Frozen: {getattr(sys, 'frozen', False)}")
    
    if getattr(sys, 'frozen', False):
        # Basis-Pfad (_internal)
        base_dir = sys._MEIPASS
        log_debug(f"Base Dir: {base_dir}")
        
        candidate_path = os.path.join(base_dir, model_name)
        log_debug(f"Candidate Path 1: {candidate_path}")
        
        final_path = None
        
        # Rekursive Suche nach config.cfg
        if os.path.exists(candidate_path):
            log_debug("Candidate 1 exists")
            # Check direct
            if os.path.exists(os.path.join(candidate_path, "config.cfg")):
                final_path = candidate_path
            else:
                # Check subdirs
                for root, dirs, files in os.walk(candidate_path):
                    if "config.cfg" in files:
                        final_path = root
                        break
        
        if final_path:
            log_debug(f"Found config at: {final_path}")
            nlp = spacy.load(final_path)
        else:
            log_debug("Config not found, trying fallback load")
            nlp = spacy.load(model_name)
    else:
        nlp = spacy.load(model_name)
        
    doc = nlp(text)

    # 1. Rollen extrahieren - Verbesserter Algorithmus für Theaterskripte
    roles = []
    
    # Strategie 1: Suche nach "Rollen:" Abschnitt und parse Bullet-Point-Format
    roles_section = re.search(r"Rollen[:\s]*(.*?)(?:\n\n|\nOrt:|\nZeit:|\nSzene|\n[A-Z]{2,}:)", text, re.DOTALL | re.IGNORECASE)
    if roles_section:
        for line in roles_section.group(1).splitlines():
            line = line.strip()
            if not line:
                continue
            bullet_match = re.match(r'^[•\-\*]\s*([A-ZÄÖÜ][A-ZÄÖÜa-zäöüß\s]+?):\s*(.*)$', line)
            if bullet_match:
                role_name = bullet_match.group(1).strip()
                if role_name and role_name not in roles:
                    roles.append(role_name)
                continue
            colon_match = re.match(r'^([A-ZÄÖÜ][A-ZÄÖÜa-zäöüß\s]+?):\s*(.*)$', line)
            if colon_match:
                role_name = colon_match.group(1).strip()
                if role_name and len(role_name.split()) <= 3 and role_name not in roles:
                    roles.append(role_name)
    
    # Strategie 2: Suche nach GROSSBUCHSTABEN-Namen
    if not roles:
        uppercase_roles = re.findall(r'^[•\-\*\s]*([A-ZÄÖÜ][A-ZÄÖÜ\s]+):\s', text, re.MULTILINE)
        for role in uppercase_roles:
            role = role.strip()
            if role and role not in roles and role.upper() not in ['SZENE', 'ORT', 'ZEIT', 'CUE', 'LICHT', 'TON', 'MUSIK', 'ROLLEN', 'DATUM']:
                roles.append(role)
    
    # Strategie 3: Pattern "• NAME:"
    if not roles:
        bullet_roles = re.findall(r'^[•\-\*]\s*([A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ\s]+?):', text, re.MULTILINE)
        for role in bullet_roles:
            role = role.strip()
            if role and role not in roles and len(role.split()) <= 3:
                roles.append(role)
    
    # Strategie 4: Fallback auf spaCy NER
    if not roles:
        spacy_roles = set(ent.text for ent in doc.ents if ent.label_ == 'PER')
        for r in spacy_roles:
            if r not in roles and len(r) > 1:
                roles.append(r)
    
    # Bereinige Rollennamen
    roles = [re.sub(r'\s*\([^)]*\)\s*', '', role).strip() for role in roles]
    roles = [role for role in roles if role]
    roles = list(dict.fromkeys(roles))

    # 2. Szenen und Dialog-Cues extrahieren
    cues = []
    current_scene = None
    current_role = None
    current_dialogue = []
    
    role_pattern_str = '|'.join([re.escape(role) for role in roles]) if roles else r'[A-ZÄÖÜ][A-ZÄÖÜa-zäöüß\s]+'
    
    dialogue_line_pattern_colon = re.compile(
        rf'^[•\-\*\s]*({role_pattern_str})(?:\s*\([^)]*\))?\s*[:：]\s*(.*)$',
        re.IGNORECASE
    )
    
    dialogue_line_pattern_no_colon = re.compile(
        rf'^({role_pattern_str})(?:\s*\([^)]*\))?\s+(.+)$',
        re.IGNORECASE
    ) if roles else None
    
    scene_pattern = re.compile(r'^(?:Szene|Scene|Akt|Act)\s*\d*\s*[:：\-–]?\s*(.*)?$', re.IGNORECASE)
    
    in_roles_section = False
    roles_section_ended = False
    
    for line in text.splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        if re.match(r'^Rollen\s*[:：]?\s*$', line_stripped, re.IGNORECASE):
            in_roles_section = True
            continue
        
        if in_roles_section:
            if re.match(r'^[•\-\*]', line_stripped) or re.match(r'^[A-ZÄÖÜ][A-ZÄÖÜa-zäöüß\s]+:', line_stripped):
                if '(' in line_stripped or len(line_stripped) > 100:
                    continue
            else:
                in_roles_section = False
                roles_section_ended = True
        
        scene_match = scene_pattern.match(line_stripped)
        if scene_match:
            if current_role and current_dialogue:
                cues.append({
                    'scene': current_scene,
                    'role': current_role,
                    'text': ' '.join(current_dialogue),
                    'uncertain': False
                })
            current_scene = line_stripped
            current_role = None
            current_dialogue = []
            continue
        
        dialogue_match = dialogue_line_pattern_colon.match(line_stripped)
        if not dialogue_match and dialogue_line_pattern_no_colon:
            dialogue_match = dialogue_line_pattern_no_colon.match(line_stripped)
        
        if dialogue_match:
            if current_role and current_dialogue:
                cues.append({
                    'scene': current_scene,
                    'role': current_role,
                    'text': ' '.join(current_dialogue),
                    'uncertain': False
                })
            
            matched_role_name = dialogue_match.group(1).strip()
            dialogue_text = dialogue_match.group(2).strip() if dialogue_match.group(2) else ''
            
            current_role = None
            for role in roles:
                if role.upper() == matched_role_name.upper():
                    current_role = role
                    break
            if not current_role:
                current_role = matched_role_name
            
            current_dialogue = [dialogue_text] if dialogue_text else []
            continue
        
        if current_role:
            current_dialogue.append(line_stripped)
        else:
            if not in_roles_section and roles_section_ended:
                is_technical = any(marker in line_stripped.lower() for marker in ['licht', 'ton', 'cue', 'musik', 'effekt', 'sound'])
                if is_technical or len(line_stripped) > 20:
                    cues.append({
                        'scene': current_scene,
                        'role': None,
                        'text': line_stripped,
                        'uncertain': True
                    })
    
    if current_role and current_dialogue:
        cues.append({
            'scene': current_scene,
            'role': current_role,
            'text': ' '.join(current_dialogue),
            'uncertain': False
        })
    
    cues = [c for c in cues if c.get('role') or c.get('text')]

    return text, cues, roles
