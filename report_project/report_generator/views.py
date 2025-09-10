from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.conf import settings
from django.template.loader import get_template
import os
import re
import tempfile
import shutil
from PyPDF2 import PdfMerger
from weasyprint import HTML, CSS
from bs4 import BeautifulSoup

def slugify(text):
    """
    Creates a URL-friendly "slug" from a string.
    Example: "Appendix A: Details" -> "appendix-a-details"
    """
    text = text.lower()
    text = re.sub(r'[\s\W_]+', '-', text) # Replace spaces and non-word chars with a hyphen
    return text.strip('-')

class ReportGeneratorView(View):
    """
    A view to handle a dynamic, two-step report generation process.
    1. Analyze HTML to find file references.
    2. Generate a consolidated PDF with appendix TOC and cover pages.
    """

    def get(self, request, *args, **kwargs):
        """
        Handles the GET request, rendering the main form.
        """
        return render(request, 'report_generator/report_form.html')

    def post(self, request, *args, **kwargs):
        """
        Delegates POST requests to the appropriate handler based on the 'action'.
        """
        action = request.POST.get('action')
        if action == 'analyze':
            return self.analyze_body(request)
        elif action == 'generate':
            return self.generate_pdf(request)
        else:
            return HttpResponse("Invalid action specified.", status=400)

    def analyze_body(self, request):
        """
        Parses the submitted HTML body to find all image, PDF, and appendix
        references and returns them as a JSON object.
        """
        html_body = request.POST.get('html_body', '')
        if not html_body:
            return JsonResponse({'images': [], 'pdfs': [], 'appendices': []})

        soup = BeautifulSoup(html_body, 'html.parser')
        
        img_tags = soup.find_all('img')
        image_sources = sorted(list(set(img.get('src') for img in img_tags if img.get('src'))))

        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
        pdf_sources = sorted(list(set(link.get('href') for link in pdf_links if link.get('href'))))
        
        # **FIX**: Return a list of objects with both title and a safe 'slug'
        appendix_tags = soup.find_all('h2', class_='appendix')
        appendices = [{'title': tag.get_text(strip=True), 'slug': slugify(tag.get_text(strip=True))} for tag in appendix_tags]

        return JsonResponse({'images': image_sources, 'pdfs': pdf_sources, 'appendices': appendices})

    def generate_pdf(self, request):
        """
        Generates the final consolidated PDF report, including a dynamically
        created appendix TOC and cover pages for each appendix.
        """
        html_body = request.POST.get('html_body', '')
        temp_dir = tempfile.mkdtemp()

        def sanitize_filename(filename):
            """Removes characters that are invalid in Windows filenames."""
            return re.sub(r'[\\/*?:"<>|]', "_", filename)

        try:
            # --- 1. Get Styling Options ---
            style_context = {
                'heading_color': request.POST.get('heading_color', '#193264'),
                'table_header_color': request.POST.get('table_header_color', '#193264'),
                'font_family': request.POST.get('font_family', 'Calibri'),
                'font_size': request.POST.get('font_size', '11'),
            }

            # --- 2. Process HTML Body and Uploaded Files ---
            soup = BeautifulSoup(html_body, 'html.parser')
            
            # Create a mapping from slug to original title for uploaded appendices
            appendix_tags = soup.find_all('h2', class_='appendix')
            appendix_map = {slugify(tag.get_text(strip=True)): tag.get_text(strip=True) for tag in appendix_tags}
            
            appendix_elements_to_remove = soup.find_all(class_='appendix')
            for element in appendix_elements_to_remove:
                next_sibling = element.find_next_sibling()
                if next_sibling and next_sibling.name == 'p':
                    if next_sibling.get_text(strip=True).startswith('['):
                        next_sibling.decompose()
                element.decompose()
            
            main_body_html = str(soup)

            for original_ref, uploaded_file in request.FILES.items():
                if original_ref in appendix_map: # Check if the file is an appendix
                    continue

                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)
                
                abs_temp_path_uri = f'file:///{os.path.abspath(temp_path).replace(os.sep, "/")}'
                main_body_html = main_body_html.replace(f'src="{original_ref}"', f'src="{abs_temp_path_uri}"')
                main_body_html = main_body_html.replace(f'href="{original_ref}"', f'href="{abs_temp_path_uri}"')

            # --- 3. Render and Generate Main Report PDF ---
            template = get_template('report_generator/template.html')
            style_context['report_body'] = main_body_html
            full_html_content = template.render(style_context)
            main_pdf_path = os.path.join(temp_dir, 'main_report.pdf')
            HTML(string=full_html_content, base_url=settings.BASE_DIR).write_pdf(main_pdf_path)

            # --- 4. Assemble Final PDF with Appendices ---
            final_pdf_path = os.path.join(temp_dir, 'consolidated_report.pdf')

            with PdfMerger() as merger:
                merger.append(main_pdf_path)
                
                # **FIX**: Check for appendix files using the slug map
                appendices_to_add = [slug for slug in appendix_map.keys() if slug in request.FILES]

                if appendices_to_add:
                    # --- 4a. Generate Appendix Table of Contents Page ---
                    toc_html_parts = [
                        '<html><head><style>',
                        '@page { size: letter; margin: 0.75in; }',
                        'body { font-family: "%s", sans-serif; }' % style_context['font_family'],
                        '.new-page { page-break-before: always; }',
                        'h1 { color: %s; font-size: 24pt; }' % style_context['heading_color'],
                        'ul { list-style-type: none; padding-left: 0; }',
                        'li { font-size: 14pt; margin-bottom: 10px; }',
                        '</style></head><body>',
                        '<div class="new-page"><h1>Appendices</h1><ul>'
                    ]
                    for slug in appendices_to_add:
                        toc_html_parts.append(f'<li>{appendix_map[slug]}</li>')
                    toc_html_parts.append('</ul></div></body></html>')
                    toc_html = "".join(toc_html_parts)
                    
                    toc_pdf_path = os.path.join(temp_dir, 'appendix_toc.pdf')
                    HTML(string=toc_html).write_pdf(toc_pdf_path)
                    merger.append(toc_pdf_path)

                    # --- 4b. Generate Cover Page and Add Each Appendix ---
                    for slug in appendices_to_add:
                        title = appendix_map[slug]
                        sanitized_title = sanitize_filename(title)
                        cover_html_parts = [
                            '<html><head><style>',
                            '@page { size: letter; margin: 0.75in; }',
                            'body { font-family: "%s", sans-serif; }' % style_context['font_family'],
                            '.cover { display: flex; align-items: center; justify-content: center; height: 100vh; page-break-before: always; }',
                            'h1 { font-size: 28pt; color: %s; }' % style_context['heading_color'],
                            '</style></head><body>',
                            f'<div class="cover"><h1>{title}</h1></div>',
                            '</body></html>'
                        ]
                        cover_html = "".join(cover_html_parts)
                        cover_pdf_path = os.path.join(temp_dir, f'cover_{sanitized_title}.pdf')
                        HTML(string=cover_html).write_pdf(cover_pdf_path)
                        merger.append(cover_pdf_path)

                        appendix_file = request.FILES[slug]
                        appendix_path = os.path.join(temp_dir, f"appendix_{sanitized_title}.pdf")
                        with open(appendix_path, 'wb+') as destination:
                            for chunk in appendix_file.chunks():
                                destination.write(chunk)
                        merger.append(appendix_path)

                merger.write(final_pdf_path)
            
            if not appendices_to_add:
                 shutil.copy(main_pdf_path, final_pdf_path)

            # --- 5. Serve the Final PDF ---
            with open(final_pdf_path, 'rb') as f:
                pdf_content = f.read()

            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="generated_report.pdf"'
            return response

        except Exception as e:
            import traceback
            traceback.print_exc()
            return HttpResponse(f"An error occurred during PDF generation: {e}", status=500)

        finally:
            shutil.rmtree(temp_dir)
