"""
iAgentPay — PDF Manual Generator
Converts manual.html to professional PDFs for all supported languages (ES, EN, ZH, HI).
"""
import os
import sys
import subprocess
import argparse
import shutil

sys.stdout.reconfigure(encoding='utf-8')

INPUT_HTML  = "manual.html"
LANGUAGES = {
    'es': 'Español',
    'en': 'English',
    'zh': 'Chinese',
    'hi': 'Hindi',
    'ar': 'Arabic',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'ja': 'Japanese',
    'de': 'German',
    'fr': 'French'
}


def generate_with_weasyprint(input_html, output_pdf):
    try:
        from weasyprint import HTML
        print(f"📄 Generating PDF with WeasyPrint...")
        os.makedirs("docs", exist_ok=True)
        HTML(filename=input_html).write_pdf(output_pdf)
        print(f"✅ PDF saved to: {output_pdf}")
        return True
    except ImportError:
        print("⚠️  WeasyPrint not installed. Run: pip install weasyprint")
        return False
    except Exception as e:
        print(f"❌ WeasyPrint error: {e}")
        return False


def generate_with_puppeteer(input_html, output_pdf):
    """Use puppeteer-cli (Node.js) to generate PDF."""
    try:
        node_check = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if node_check.returncode != 0:
            print("⚠️  Node.js not found. Install from https://nodejs.org/")
            return False
    except Exception as e:
        print(f"⚠️  Node.js check failed: {e}")
        return False

    os.makedirs("docs", exist_ok=True)
    abs_html = os.path.abspath(input_html)
    abs_pdf  = os.path.abspath(output_pdf)

    print(f"📄 Generating PDF with Puppeteer...")
    try:
        result = subprocess.run(
            ["npx", "puppeteer-cli", "print", abs_html, abs_pdf,
             "--format", "A4", "--margin-top", "20px", "--margin-bottom", "20px"],
            capture_output=True, text=True, shell=True
        )
        if result.returncode == 0 and os.path.exists(abs_pdf):
            print(f"✅ PDF saved to: {output_pdf}")
            return True
        else:
            print(f"❌ Puppeteer error or file not generated. Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Puppeteer execution failed: {e}")
        return False


def generate_with_chrome(input_html, output_pdf):
    """Use headless Chrome/Chromium as last resort."""
    try:
        chrome_candidates = [
            "google-chrome", "google-chrome-stable",
            "chromium", "chromium-browser",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        chrome_bin = None
        for candidate in chrome_candidates:
            try:
                result = subprocess.run(["where" if sys.platform == "win32" else "which", candidate],
                                        capture_output=True, text=True)
                if result.returncode == 0 or os.path.exists(candidate):
                    chrome_bin = candidate
                    break
            except Exception:
                if os.path.exists(candidate):
                    chrome_bin = candidate
                    break

        if not chrome_bin:
            print("⚠️  Chrome/Chromium not found.")
            return False

        os.makedirs("docs", exist_ok=True)
        abs_html = f"file:///{os.path.abspath(input_html).replace(os.sep, '/')}"
        abs_pdf  = os.path.abspath(output_pdf)

        print(f"📄 Generating PDF with headless Chrome...")
        result = subprocess.run([
            chrome_bin,
            "--headless=new",
            "--no-sandbox",
            "--disable-gpu",
            f"--print-to-pdf={abs_pdf}",
            "--print-to-pdf-no-header",
            abs_html
        ], capture_output=True, text=True)

        if result.returncode == 0 and os.path.exists(abs_pdf):
            print(f"✅ PDF saved to: {output_pdf}")
            return True
        else:
            print(f"❌ Chrome error: {result.stderr[:200]}")
            return False
    except Exception as e:
        print(f"❌ Chrome execution failed: {e}")
        return False


def generate_for_language(lang, engine="auto"):
    print(f"\n🌐 Processing language: {LANGUAGES[lang].upper()} ({lang})")
    
    # 1. Read source HTML
    with open(INPUT_HTML, "r", encoding="utf-8") as f:
        original_html = f.read()

    # 2. Modify to make this language active
    # Disable default Spanish active class
    modified_html = original_html.replace('id="content-es" class="lang-content active"', 'id="content-es" class="lang-content"')
    # Enable the target language active class
    target_id = f'id="content-{lang}" class="lang-content"'
    if target_id in modified_html:
        modified_html = modified_html.replace(target_id, f'id="content-{lang}" class="lang-content active"')
    else:
        # Fallback
        modified_html = modified_html.replace(f'id="content-{lang}"', f'id="content-{lang}" class="lang-content active"')

    # 3. Write temp HTML file
    temp_html = f"temp_manual_{lang}.html"
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write(modified_html)

    # 4. Generate PDF path
    output_pdf = f"docs/MANUAL_iAgentPay_v8_{lang}.pdf"
    
    # Remove existing PDF to ensure clean generation
    if os.path.exists(output_pdf):
        try:
            os.remove(output_pdf)
        except Exception:
            pass

    success = False
    try:
        if engine == "weasyprint":
            success = generate_with_weasyprint(temp_html, output_pdf)
        elif engine == "puppeteer":
            success = generate_with_puppeteer(temp_html, output_pdf)
        elif engine == "chrome":
            success = generate_with_chrome(temp_html, output_pdf)
        else:
            # Auto
            success = (
                generate_with_weasyprint(temp_html, output_pdf) or
                generate_with_puppeteer(temp_html, output_pdf) or
                generate_with_chrome(temp_html, output_pdf)
            )
    finally:
        # 5. Clean up temp HTML
        if os.path.exists(temp_html):
            try:
                os.remove(temp_html)
            except Exception:
                pass

    if success:
        print(f"✨ Successfully generated: {output_pdf}")
        # Copy Spanish version to legacy non-suffix path for compatibility
        if lang == 'es':
            legacy_pdf = "docs/MANUAL_iAgentPay_v8.pdf"
            try:
                shutil.copy(output_pdf, legacy_pdf)
                print(f"✅ Copied Spanish manual as legacy fallback to: {legacy_pdf}")
            except Exception as e:
                print(f"⚠️ Failed to copy legacy fallback: {e}")
    else:
        print(f"💥 Failed to generate PDF for: {lang}")
    return success


def main():
    parser = argparse.ArgumentParser(description="iAgentPay PDF Manual Generator")
    parser.add_argument("--engine", choices=["weasyprint", "puppeteer", "chrome", "auto"],
                        default="auto", help="PDF engine to use")
    parser.add_argument("--lang", choices=["all", "es", "en", "zh", "hi", "ar", "pt", "ru", "ja", "de", "fr"], default="all",
                        help="Specific language to generate, or 'all'")
    args = parser.parse_args()

    print("=" * 60)
    print("  iAgentPay v8.0 — Multi-Language PDF Manual Generator")
    print("=" * 60)

    langs_to_process = LANGUAGES.keys() if args.lang == "all" else [args.lang]

    all_success = True
    for lang in langs_to_process:
        success = generate_for_language(lang, args.engine)
        if not success:
            all_success = False

    if not all_success:
        sys.exit(1)

    print("\n🎉 Multi-language PDF manual generation completed successfully!")


if __name__ == "__main__":
    main()
