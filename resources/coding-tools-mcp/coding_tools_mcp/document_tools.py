from __future__ import annotations

import html
import hashlib
import io
import re
import zipfile
from pathlib import Path
from typing import Any

from .errors import ToolFailure
from xml.etree import ElementTree as ET


WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _safe_text(value: Any, limit: int = 2_000_000) -> str:
    return str(value or "")[:limit]


def extract_docx(path: Path, max_chars: int = 200_000) -> dict[str, Any]:
    paragraphs: list[str] = []
    with zipfile.ZipFile(path) as archive:
        data = archive.read("word/document.xml")
        media = [
            {"name": name, "size": archive.getinfo(name).file_size}
            for name in archive.namelist()
            if name.startswith("word/media/") and not name.endswith("/")
        ]
    root = ET.fromstring(data)
    for paragraph in root.iter(f"{{{WORD_NS}}}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{{{WORD_NS}}}t")).strip()
        if text:
            paragraphs.append(text)
    content = "\n".join(paragraphs)
    return {
        "format": "docx",
        "content": content[:max_chars],
        "paragraph_count": len(paragraphs),
        "embedded_media": media[:100],
        "embedded_media_count": len(media),
        "truncated": len(content) > max_chars,
    }


def extract_pdf(path: Path, max_chars: int = 200_000) -> dict[str, Any]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF support is unavailable because the bundled pypdf package is missing.") from exc
    reader = PdfReader(str(path))
    pages: list[str] = []
    page_layout: list[dict[str, Any]] = []
    embedded_images: list[dict[str, Any]] = []
    total = 0
    truncated = False
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
        except (TypeError, ValueError):
            width = height = 0.0
        page_images: list[str] = []
        try:
            for image in page.images:
                name = str(getattr(image, "name", "") or f"page-{page_number}-image")
                page_images.append(name)
                embedded_images.append({"page": page_number, "name": name})
        except Exception:
            pass
        page_layout.append({"page": page_number, "width_points": round(width, 2), "height_points": round(height, 2), "embedded_image_count": len(page_images)})
        text = page.extract_text() or ""
        remaining = max_chars - total
        if remaining <= 0:
            truncated = True
            break
        pages.append(text[:remaining])
        total += min(len(text), remaining)
        if len(text) > remaining:
            truncated = True
            break
    return {
        "format": "pdf",
        "content": "\n\n".join(pages),
        "page_count": len(reader.pages),
        "pages_extracted": len(pages),
        "page_layout": page_layout[:200],
        "embedded_images": embedded_images[:200],
        "embedded_image_count": len(embedded_images),
        "truncated": truncated or len(pages) < len(reader.pages),
    }


def extract_document(path: Path, max_chars: int = 200_000) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if suffix == ".docx":
        result = extract_docx(path, max_chars)
    elif suffix == ".pdf":
        result = extract_pdf(path, max_chars)
    elif suffix in {".txt", ".md", ".csv", ".json", ".xml", ".html", ".htm"}:
        content = path.read_text(encoding="utf-8", errors="replace")
        result = {"format": suffix.removeprefix("."), "content": content[:max_chars], "truncated": len(content) > max_chars}
    else:
        raise ValueError(f"Unsupported document format: {suffix or '<none>'}")
    result.update({"path": str(path), "size": path.stat().st_size})
    return result


def _paragraph_xml(text: str, style: str = "") -> str:
    value = html.escape(text)
    props = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f'<w:p>{props}<w:r><w:t xml:space="preserve">{value}</w:t></w:r></w:p>'


def _document_xml(title: str, content: str) -> str:
    blocks: list[str] = []
    if title.strip():
        blocks.append(_paragraph_xml(title.strip(), "Title"))
    for raw in _safe_text(content).splitlines():
        line = raw.rstrip()
        if not line:
            blocks.append("<w:p/>")
        elif line.startswith("### "):
            blocks.append(_paragraph_xml(line[4:], "Heading3"))
        elif line.startswith("## "):
            blocks.append(_paragraph_xml(line[3:], "Heading2"))
        elif line.startswith("# "):
            blocks.append(_paragraph_xml(line[2:], "Heading1"))
        elif re.match(r"^\s*[-*]\s+", line):
            blocks.append(_paragraph_xml("• " + re.sub(r"^\s*[-*]\s+", "", line)))
        else:
            blocks.append(_paragraph_xml(line))
    body = "".join(blocks) + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134"/></w:sectPr>'
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' \
        f'<w:document xmlns:w="{WORD_NS}"><w:body>{body}</w:body></w:document>'


def create_docx(path: Path, title: str, content: str, *, overwrite: bool = False) -> dict[str, Any]:
    if path.exists() and not overwrite:
        raise FileExistsError(f"Target already exists: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>'''
    rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''
    doc_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>'''
    styles = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{WORD_NS}">
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:ascii="Aptos" w:eastAsia="Microsoft YaHei"/><w:sz w:val="21"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="25"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="23"/></w:rPr></w:style>
</w:styles>'''
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", rels)
        archive.writestr("word/_rels/document.xml.rels", doc_rels)
        archive.writestr("word/styles.xml", styles)
        archive.writestr("word/document.xml", _document_xml(title, content))
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_bytes(buffer.getvalue())
    temp.replace(path)
    return {"format": "docx", "path": str(path), "size": path.stat().st_size}


def create_text_document(path: Path, content: str, *, overwrite: bool = False) -> dict[str, Any]:
    """Write generated Markdown or plain text atomically and return verification metadata."""
    suffix = path.suffix.lower()
    if suffix not in {".md", ".txt"}:
        raise ValueError("Text document target must end with .md or .txt.")
    if path.exists() and not overwrite:
        raise FileExistsError(f"Target already exists: {path.name}")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _safe_text(content).encode("utf-8")
    temp = path.with_name(f".{path.name}.tmp")
    temp.write_bytes(data)
    temp.replace(path)
    text = data.decode("utf-8")
    return {
        "format": suffix.removeprefix("."),
        "path": str(path),
        "size": len(data),
        "line_count": len(text.splitlines()),
        "sha256": hashlib.sha256(data).hexdigest(),
        "preview": text.splitlines()[:8],
    }


def convert_document(source: Path, target: Path, *, overwrite: bool = False) -> dict[str, Any]:
    if target.suffix.lower() != ".docx":
        raise ValueError("The current document converter outputs .docx files only.")
    extracted = extract_document(source)
    created = create_docx(target, source.stem, str(extracted.get("content", "")), overwrite=overwrite)
    return {"source": str(source), "target": created["path"], "source_format": extracted["format"], "size": created["size"]}


class DocumentToolsMixin:
    def document_workflow(self, args: dict[str, Any]) -> dict[str, Any]:
        action = str(args.get("action", "inspect")).lower()
        detail = str(args.get("detail", "compact")).lower()
        capabilities = {
            "runtime_ready": True,
            "dependency_check_required": False,
            "supported_inputs": ["pdf", "docx", "txt", "md", "csv", "json", "xml", "html"],
            "supported_output": ["docx", "md", "txt"],
            "extracts_pdf_page_sizes": True,
            "detects_embedded_images": True,
            "editable_layout_fidelity": "basic",
            "note": "Text and embedded-media structure are inspected locally. Pixel-perfect editable PDF-to-Word reconstruction is not guaranteed.",
        }
        if action == "capabilities":
            return {"capabilities": capabilities}
        if action == "inspect":
            raw_paths = args.get("paths", [])
            single = str(args.get("path", "")).strip()
            paths = [single] if single else []
            paths.extend(str(item).strip() for item in raw_paths if str(item).strip())
            paths = list(dict.fromkeys(paths))[:20]
            if not paths:
                raise ToolFailure("INVALID_ARGUMENT", "path or paths is required for document inspection.", category="validation")
            resolved_paths = [self.resolve_existing(raw_path).path for raw_path in paths]
            cache_key = self._fast_cache_key(
                "document_workflow_inspect",
                {"paths": paths, "max_chars": int(args.get("max_chars", 200000)), "detail": detail},
                file_paths=resolved_paths,
            )
            cached = self._fast_cache_get(cache_key, 300)
            if cached is not None:
                return cached
            documents: list[dict[str, Any]] = []
            for raw_path in paths:
                try:
                    document = self.document_extract({"path": raw_path, "max_chars": int(args.get("max_chars", 200000))})
                    if detail != "layout":
                        document = {key: document.get(key) for key in (
                            "path", "format", "suffix", "size", "page_count", "content", "truncated"
                        ) if key in document}
                    documents.append(document)
                except ToolFailure as exc:
                    documents.append({"path": raw_path, "ok": False, "error": {"code": exc.code, "message": exc.message}})
            payload = {
                "action": action,
                "documents": documents,
                "count": len(documents),
                "detail": detail,
                "recommended_next_action": "Reason over this content once, then call document_workflow action=create once. Do not inspect dependencies, repeat extraction, use exec_command/apply_patch, or run a separate verification command.",
                "cache": {"hit": False, "age_ms": 0},
            }
            if detail == "layout":
                payload["capabilities"] = capabilities
            self._fast_cache_put(cache_key, payload)
            return payload
        if action == "create":
            dedup_key = self._fast_cache_key("document_workflow_create", args)
            cached_create = self._fast_cache_get(dedup_key, 30)
            if cached_create is not None:
                cached_create["deduplicated"] = True
                return cached_create
            target = self.resolve_for_write(str(args.get("target", args.get("path", ""))))
            if target.path.suffix.lower() in {".md", ".txt"}:
                try:
                    result = create_text_document(
                        target.path,
                        str(args.get("content", "")),
                        overwrite=bool(args.get("overwrite", False)),
                    )
                except (OSError, ValueError) as exc:
                    raise ToolFailure("DOCUMENT_WRITE_FAILED", str(exc), category="runtime", retryable=True) from exc
                result["path"] = target.display
                result["affected_files"] = [{"path": target.display, "operation": "create"}]
            else:
                result = self.document_create({
                    "path": target.display,
                    "title": args.get("title", ""),
                    "content": args.get("content", ""),
                    "overwrite": args.get("overwrite", False),
                })
            self._invalidate_fast_cache()
            payload = {"action": action, "result": result, "affected_files": result.get("affected_files", [])}
            self._fast_cache_put(dedup_key, payload)
            return payload
        if action == "convert":
            result = self.document_convert({
                "source": args.get("source", ""),
                "target": args.get("target", ""),
                "overwrite": args.get("overwrite", False),
            })
            self._invalidate_fast_cache()
            return {"action": action, "result": result, "affected_files": result.get("affected_files", [])}
        if action == "rebuild":
            source = self.resolve_existing(str(args.get("source", "")))
            target = self.resolve_for_write(str(args.get("target", "")))
            analysis = extract_document(source.path, min(int(args.get("max_chars", 200000)), 1000000))
            content = str(args.get("content", ""))
            if not content:
                content = str(analysis.get("content", ""))
            title = str(args.get("title", "")).strip() or source.path.stem
            result = create_docx(target.path, title, content, overwrite=bool(args.get("overwrite", False)))
            result["path"] = target.display
            affected = [{"path": target.display, "operation": "create"}]
            self._invalidate_fast_cache()
            return {
                "action": action,
                "source_analysis": analysis,
                "result": result,
                "affected_files": affected,
                "capabilities": capabilities,
                "fidelity_warning": capabilities["note"],
            }
        raise ToolFailure("INVALID_ARGUMENT", f"Unknown document workflow action: {action}", category="validation")

    def document_extract(self, args: dict[str, Any]) -> dict[str, Any]:
        resolved = self.resolve_existing(str(args.get("path", "")))
        if not resolved.path.is_file():
            raise ToolFailure("NOT_A_FILE", "Document path must be a file.", category="validation")
        try:
            return extract_document(resolved.path, min(int(args.get("max_chars", 200000)), 1000000))
        except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
            raise ToolFailure("DOCUMENT_READ_FAILED", str(exc), category="runtime", retryable=True) from exc

    def document_create(self, args: dict[str, Any]) -> dict[str, Any]:
        resolved = self.resolve_for_write(str(args.get("path", "")))
        if resolved.path.suffix.lower() != ".docx":
            raise ToolFailure("INVALID_ARGUMENT", "document_create target must end with .docx.", category="validation")
        try:
            result = create_docx(resolved.path, str(args.get("title", "")), str(args.get("content", "")), overwrite=bool(args.get("overwrite", False)))
        except (OSError, ValueError) as exc:
            raise ToolFailure("DOCUMENT_WRITE_FAILED", str(exc), category="runtime", retryable=True) from exc
        result["path"] = resolved.display
        result["affected_files"] = [{"path": resolved.display, "operation": "create"}]
        return result

    def document_convert(self, args: dict[str, Any]) -> dict[str, Any]:
        source = self.resolve_existing(str(args.get("source", "")))
        target = self.resolve_for_write(str(args.get("target", "")))
        try:
            result = convert_document(source.path, target.path, overwrite=bool(args.get("overwrite", False)))
        except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
            raise ToolFailure("DOCUMENT_CONVERT_FAILED", str(exc), category="runtime", retryable=True) from exc
        result["source"] = source.display
        result["target"] = target.display
        result["affected_files"] = [{"path": target.display, "operation": "create"}]
        return result

