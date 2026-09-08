import zipfile
import io
import xml.sax.saxutils as saxutils

DOCX_I18N = {
    "ES": {
        "title_default": "GUION CINEMATOGRÁFICO",
        "format_default": "LARGOMETRAJE",
        "author_label": "Escrito por Visionary Agent (Studio Co-Director AI)",
        "genre_label": "Género",
        "format_label": "Formato",
        "cast_heading": "PERSONAJES / REPARTO:",
        "scene_label": "ESCENA",
        "note_label": "Nota de Dirección:",
        "fade_in": "FADE IN:",
        "cut_to": "CORTE A:"
    },
    "EN": {
        "title_default": "SCREENPLAY",
        "format_default": "FEATURE FILM",
        "author_label": "Written by Visionary Agent (Studio Co-Director AI)",
        "genre_label": "Genre",
        "format_label": "Format",
        "cast_heading": "CHARACTERS / CAST:",
        "scene_label": "SCENE",
        "note_label": "Director's Note:",
        "fade_in": "FADE IN:",
        "cut_to": "CUT TO:"
    },
    "FR": {
        "title_default": "SCÉNARIO CINÉMATOGRAPHIQUE",
        "format_default": "LONG MÉTRAGE",
        "author_label": "Écrit par Visionary Agent (Studio Co-Director AI)",
        "genre_label": "Genre",
        "format_label": "Format",
        "cast_heading": "PERSONNAGES / DISTRIBUTION:",
        "scene_label": "SCÈNE",
        "note_label": "Note d'Intention:",
        "fade_in": "OUVERTURE EN FONDU:",
        "cut_to": "COUPE À:"
    },
    "DE": {
        "title_default": "DREHBUCH",
        "format_default": "SPIELFILM",
        "author_label": "Geschrieben von Visionary Agent (Studio Co-Director AI)",
        "genre_label": "Genre",
        "format_label": "Format",
        "cast_heading": "FIGUREN / BESETZUNG:",
        "scene_label": "SZENE",
        "note_label": "Regieanmerkung:",
        "fade_in": "AUFBLENDE:",
        "cut_to": "SCHNITT ZU:"
    },
    "IT": {
        "title_default": "SCENEGGIATURA CINEMATOGRAFICA",
        "format_default": "LUNGOMETRAGGIO",
        "author_label": "Scritto da Visionary Agent (Studio Co-Director AI)",
        "genre_label": "Genere",
        "format_label": "Formato",
        "cast_heading": "PERSONAGGI / CAST:",
        "scene_label": "SCENA",
        "note_label": "Nota di Regia:",
        "fade_in": "DISSOLVENZA IN ENTRATA:",
        "cut_to": "STACCO SU:"
    },
    "PT": {
        "title_default": "ROTEIRO CINEMATOGRÁFICO",
        "format_default": "LONGA-METRAGEM",
        "author_label": "Escrito por Visionary Agent (Studio Co-Director AI)",
        "genre_label": "Gênero",
        "format_label": "Formato",
        "cast_heading": "PERSONAGENS / ELENCO:",
        "scene_label": "CENA",
        "note_label": "Nota de Direção:",
        "fade_in": "FADE IN:",
        "cut_to": "CORTE PARA:"
    }
}

def create_screenplay_docx(project: dict, scenes: list, characters: list = None, lang: str = "ES") -> bytes:
    """Generates a genuine standard Microsoft Word .docx binary file containing the complete screenplay."""
    lang = (lang or "ES").upper()
    is_en = (lang == "EN")
    i18n = DOCX_I18N.get(lang, DOCX_I18N["ES"])

    # Auto-detect if argument order was inverted (project, characters, scenes)
    if characters is not None and len(scenes) > 0 and "role" in scenes[0] and len(characters) > 0 and ("scene_number" in characters[0] or "slugline" in characters[0]):
        scenes, characters = characters, scenes
    elif characters is None:
        characters = []

    title = saxutils.escape(project.get("title", i18n["title_default"]))
    logline = saxutils.escape(project.get("logline", ""))
    genre = saxutils.escape(project.get("genre", "Drama"))
    format_type = saxutils.escape(project.get("format", i18n["format_default"]))

    author_label = i18n["author_label"]
    genre_label = i18n["genre_label"]
    format_label = i18n["format_label"]
    cast_heading = i18n["cast_heading"]
    scene_label = i18n["scene_label"]
    note_label = i18n["note_label"]
    fade_in_label = i18n["fade_in"]

    # Build document.xml paragraphs
    doc_body_xml = []

    # Title Page
    doc_body_xml.append(f"""
    <w:p>
      <w:pPr><w:jc w:val="center"/><w:spacing w:before="3600" w:after="400"/></w:pPr>
      <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:b/><w:sz w:val="48"/><w:color w:val="1A1A1A"/></w:rPr><w:t>{title.upper()}</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:jc w:val="center"/><w:spacing w:after="2400"/></w:pPr>
      <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:sz w:val="24"/><w:color w:val="666666"/></w:rPr><w:t>{author_label}</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:jc w:val="center"/><w:spacing w:after="400"/></w:pPr>
      <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:sz w:val="22"/><w:color w:val="444444"/></w:rPr><w:t>{genre_label}: {genre} | {format_label}: {format_type}</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:jc w:val="center"/><w:spacing w:after="1200"/></w:pPr>
      <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:i/><w:sz w:val="20"/><w:color w:val="555555"/></w:rPr><w:t>"{logline}"</w:t></w:r>
    </w:p>
    <w:p><w:r><w:br w:type="page"/></w:r></w:p>
    """)

    # Cast Page
    doc_body_xml.append(f"""
    <w:p>
      <w:pPr><w:spacing w:before="600" w:after="400"/></w:pPr>
      <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:b/><w:sz w:val="28"/></w:rPr><w:t>{cast_heading}</w:t></w:r>
    </w:p>
    """)
    for c in characters:
        c_name = saxutils.escape(c.get("name", "CHARACTER" if is_en else "PERSONAJE"))
        c_role = saxutils.escape(c.get("role", "Role" if is_en else "Rol"))
        c_desc = saxutils.escape(c.get("personality", c.get("motivation", "")))
        doc_body_xml.append(f"""
        <w:p>
          <w:pPr><w:spacing w:after="200"/></w:pPr>
          <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:b/><w:sz w:val="22"/></w:rPr><w:t>{c_name}</w:t></w:r>
          <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:sz w:val="20"/></w:rPr><w:t> ({c_role}): {c_desc}</w:t></w:r>
        </w:p>
        """)

    doc_body_xml.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

    # Scenes
    for s in scenes:
        sc_num = s.get("scene_number", 1)
        slug_raw = s.get("slugline", f"{scene_label} {sc_num}")
        slug = saxutils.escape(slug_raw)
        summary = saxutils.escape(s.get("summary", ""))
        subtext = saxutils.escape(s.get("subtext", ""))
        script_text = s.get("script_text", "")

        # Slugline
        doc_body_xml.append(f"""
        <w:p>
          <w:pPr><w:spacing w:before="600" w:after="200"/><w:keepNext/></w:pPr>
          <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:b/><w:sz w:val="24"/></w:rPr><w:t>{scene_label} {sc_num}: {slug.upper()}</w:t></w:r>
        </w:p>
        <w:p>
          <w:pPr><w:spacing w:after="160"/></w:pPr>
          <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:sz w:val="22"/></w:rPr><w:t>{fade_in_label}</w:t></w:r>
        </w:p>
        <w:p>
          <w:pPr><w:spacing w:after="240"/></w:pPr>
          <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:sz w:val="22"/></w:rPr><w:t>{summary}</w:t></w:r>
        </w:p>
        """)

        if subtext:
            doc_body_xml.append(f"""
            <w:p>
              <w:pPr><w:spacing w:after="200"/></w:pPr>
              <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:i/><w:sz w:val="20"/><w:color w:val="555555"/></w:rPr><w:t>[{note_label} {subtext}]</w:t></w:r>
            </w:p>
            """)

        # Script text lines
        if script_text:
            for line in script_text.splitlines():
                l_str = line.strip()
                if not l_str:
                    continue
                safe_l = saxutils.escape(l_str)
                # Check if it looks like character cue (all uppercase)
                if safe_l.isupper() and len(safe_l) < 35 and not any(w in safe_l for w in ["INT.", "EXT.", "CUT TO:", "FADE IN:"]):
                    doc_body_xml.append(f"""
                    <w:p>
                      <w:pPr><w:ind w:left="2880"/><w:spacing w:before="240" w:after="60"/><w:keepNext/></w:pPr>
                      <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:b/><w:sz w:val="22"/></w:rPr><w:t>{safe_l}</w:t></w:r>
                    </w:p>
                    """)
                elif safe_l.startswith("(") and safe_l.endswith(")"):
                    doc_body_xml.append(f"""
                    <w:p>
                      <w:pPr><w:ind w:left="2160"/><w:spacing w:after="60"/><w:keepNext/></w:pPr>
                      <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:i/><w:sz w:val="22"/></w:rPr><w:t>{safe_l}</w:t></w:r>
                    </w:p>
                    """)
                else:
                    doc_body_xml.append(f"""
                    <w:p>
                      <w:pPr><w:ind w:left="1440" w:right="1440"/><w:spacing w:after="160"/></w:pPr>
                      <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:sz w:val="22"/></w:rPr><w:t>{safe_l}</w:t></w:r>
                    </w:p>
                    """)

        doc_body_xml.append("""
        <w:p>
          <w:pPr><w:jc w:val="right"/><w:spacing w:before="200" w:after="400"/></w:pPr>
          <w:r><w:rPr><w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime"/><w:b/><w:sz w:val="22"/><w:color w:val="888888"/></w:rPr><w:t>CUT TO:</w:t></w:r>
        </w:p>
        """)

    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:body>
        {''.join(doc_body_xml)}
        <w:sectPr>
          <w:pgSz w:w="12240" w:h="15840"/>
          <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="2160" w:header="720" w:footer="720" w:gutter="0"/>
        </w:sectPr>
      </w:body>
    </w:document>"""

    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
      <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
      <Default Extension="xml" ContentType="application/xml"/>
      <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
      <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
    </Types>"""

    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
      <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
    </Relationships>"""

    doc_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
      <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
    </Relationships>"""

    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
      <w:docDefaults>
        <w:rPrDefault>
          <w:rPr>
            <w:rFonts w:ascii="Courier Prime" w:hAnsi="Courier Prime" w:cs="Courier Prime"/>
            <w:sz w:val="24"/>
            <w:lang w:val="es-ES"/>
          </w:rPr>
        </w:rPrDefault>
      </w:docDefaults>
    </w:styles>"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("_rels/.rels", rels_xml)
        zf.writestr("word/_rels/document.xml.rels", doc_rels_xml)
        zf.writestr("word/styles.xml", styles_xml)
        zf.writestr("word/document.xml", document_xml)

    return buf.getvalue()
