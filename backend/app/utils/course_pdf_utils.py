import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from ..services.mongo import get_course

class CoursePDFUtils:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()
    
    def _setup_styles(self):
        """Setup basic styles for the PDF"""
        # Title style
        self.title_style = ParagraphStyle(
            'Title',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=20,
            textColor=HexColor('#1976d2'),
            alignment=1  # Center alignment
        )
        
        # Course info style
        self.info_style = ParagraphStyle(
            'Info',
            parent=self.styles['Normal'],
            fontSize=14,
            spaceAfter=10,
            alignment=0  # Left alignment
        )
        
        # Description style
        self.desc_style = ParagraphStyle(
            'Description',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=8,
            leading=16
        )
        
        # Footer style
        self.footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=HexColor('#666666'),
            alignment=1  # Center alignment
        )
    
    def get_course_info(self, course_id):
        try:
            # Get course data from MongoDB
            course_data = get_course(course_id)
            
            if not course_data:
                print(f"Course not found: {course_id}")
                return None
            
            return course_data
            
        except Exception as e:
            print(f"Error getting course info: {str(e)}")
            return None
    
    def create_course_pdf(self, course_id, output_filename=None):
        try:
            # Get course information
            course_data = self.get_course_info(course_id)
            
            if not course_data:
                print("Could not retrieve course information")
                return None
            
            # Extract course details
            course_name = course_data.get('name', 'Unknown Course')
            course_description = course_data.get('description', 'No description available')
            
            # Generate filename if not provided
            if not output_filename:
                # Replace spaces with underscores and ensure proper format
                safe_course_name = course_name.replace(' ', '_')
                output_filename = f"{safe_course_name}_Course_Description.pdf"
            
            # Ensure filename has .pdf extension
            if not output_filename.lower().endswith('.pdf'):
                output_filename += '.pdf'
            
            # Create output directory
            output_dir = os.path.join(os.getcwd(), 'local_storage', 'course_pdfs')
            os.makedirs(output_dir, exist_ok=True)
            
            # Full path for the PDF file
            pdf_path = os.path.join(output_dir, output_filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            # Build PDF content
            story = []
            
            # Add title
            title = Paragraph("Course Information", self.title_style)
            story.append(title)
            story.append(Spacer(1, 20))
            
            # Add course name
            course_name_para = Paragraph(f"<b>Course Name:</b> {course_name}", self.info_style)
            story.append(course_name_para)
            story.append(Spacer(1, 15))
            
            # Add course description
            story.append(Paragraph("<b>Course Description:</b>", self.info_style))
            story.append(Spacer(1, 5))
            
            # Add description text
            desc_para = Paragraph(course_description, self.desc_style)
            story.append(desc_para)
            story.append(Spacer(1, 20))
            
            # Add metadata
            story.append(Paragraph("<b>Course Details:</b>", self.info_style))
            story.append(Spacer(1, 5))
            
            story.append(Paragraph(f"<b>Course ID:</b> {course_id}", self.desc_style))
            story.append(Spacer(1, 20))
            
            # Add footer
            footer_text = f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
            footer = Paragraph(footer_text, self.footer_style)
            story.append(footer)
            
            # Build PDF
            doc.build(story)
            
            print(f"PDF created successfully: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"Error creating PDF: {str(e)}")
            return None

# Create a global instance for easy use
course_pdf_utils = CoursePDFUtils()

# Function to use the utility
def generate_course_pdf(course_id):
    return course_pdf_utils.create_course_pdf(course_id)