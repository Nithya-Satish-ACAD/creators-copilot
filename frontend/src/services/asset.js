import axios from 'axios';
import jsPDF from 'jspdf';

const baseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';
const API_BASE = new URL('/api', baseUrl).toString();

function getToken() {
  const token = localStorage.getItem('token');
  if (!token || token === 'null') {
    throw new Error('User not authenticated. Please log in.');
  }
  return token;
}

function handleAxiosError(error) {
  if (error.response && error.response.data && error.response.data.detail) {
    throw new Error(error.response.data.detail);
  }
  throw new Error(error.message || 'Unknown error');
}

export const assetService = {
  // Get all assets for a course
  getAssets: async (courseId) => {
    try {
      const res = await axios.get(`${API_BASE}/courses/${courseId}/assets`, {
        headers: {
          'Authorization': `Bearer ${getToken()}`
        }
      });
      return res.data;
    } catch (error) {
      handleAxiosError(error);
    }
  },

  // Create initial asset chat with selected files
  createAssetChat: async (courseId, assetTypeName, fileNames) => {
    try {
      const res = await axios.post(`${API_BASE}/courses/${courseId}/asset_chat/${assetTypeName}`, 
        { file_names: fileNames }, 
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getToken()}`
          }
        }
      );
      return res.data;
    } catch (error) {
      handleAxiosError(error);
    }
  },

  // Continue asset chat conversation
  continueAssetChat: async (courseId, assetName, threadId, userPrompt) => {
    try {
      const res = await axios.put(`${API_BASE}/courses/${courseId}/asset_chat/${assetName}?thread_id=${threadId}`, 
        { user_prompt: userPrompt }, 
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getToken()}`
          }
        }
      );
      return res.data;
    } catch (error) {
      handleAxiosError(error);
    }
  },

  // Save asset to database
  saveAsset: async (courseId, assetName, assetType, content) => {
    try {
      const res = await axios.post(`${API_BASE}/courses/${courseId}/assets`, 
        { content: content }, 
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${getToken()}`
          },
          params: {
            asset_name: assetName,
            asset_type: assetType
          }
        }
      );
      return res.data;
    } catch (error) {
      handleAxiosError(error);
    }
  },

  // View asset content
  viewAsset: async (courseId, assetName) => {
    try {
      const res = await axios.get(`${API_BASE}/courses/${courseId}/assets/${assetName}/view`, {
        headers: {
          'Authorization': `Bearer ${getToken()}`
        }
      });
      return res.data;
    } catch (error) {
      handleAxiosError(error);
    }
  },

  // Download asset as PDF file
  downloadAsset: async (courseId, assetName) => {
    try {
      // Validate inputs
      if (!courseId || !assetName) {
        throw new Error('Course ID and Asset Name are required');
      }

      const res = await axios.get(`${API_BASE}/courses/${courseId}/assets/${assetName}/view`, {
        headers: {
          'Authorization': `Bearer ${getToken()}`
        }
      });
      
      const asset = res.data;
      
      // Validate asset data
      if (!asset || !asset.asset_content) {
        throw new Error('Invalid asset data received from server');
      }

      const pdf = new jsPDF();
      
      // Enhanced markdown parser class with better error handling
      class MarkdownToPDF {
        constructor(pdf) {
          this.pdf = pdf;
          this.margin = 20;
          // Dynamic page metrics
          const pageWidth = this.pdf.internal.pageSize.getWidth();
          const pageHeight = this.pdf.internal.pageSize.getHeight();
          this.pageWidth = pageWidth;
          // Leave space for footer
          this.pageHeight = pageHeight - 20;
          this.maxWidth = pageWidth - (this.margin * 2);
          this.yPosition = Math.max(80, this.margin);
          this.lineHeight = 6;
          this.currentFontSize = 12;
        }
        
        // Replace problematic Unicode characters with ASCII-friendly equivalents
        normalizeToAscii(text) {
          if (text == null) return '';
          return text
            .toString()
            // smart quotes → straight quotes
            .replace(/[\u2018\u2019]/g, "'")
            .replace(/[\u201C\u201D]/g, '"')
            // dashes → hyphen
            .replace(/[\u2013\u2014]/g, '-')
            // bullet and middle dot → hyphen
            .replace(/[\u2022\u00B7]/g, '-')
            // ellipsis
            .replace(/[\u2026]/g, '...')
            // non-breaking spaces and narrow spaces → regular space
            .replace(/[\u00A0\u202F\u2009]/g, ' ')
            // zero width space → remove
            .replace(/[\u200B]/g, '');
        }

        // Improve wrapping for long words without spaces
        softWrapLongWords(text) {
          if (!text) return '';
          const SOFT_BREAK_EVERY = 18;
          return text
            .split(/(\s+)/)
            .map(token => {
              if (/\s+/.test(token)) return token;
              if (token.length <= SOFT_BREAK_EVERY) return token;
              const parts = [];
              for (let i = 0; i < token.length; i += SOFT_BREAK_EVERY) {
                parts.push(token.slice(i, i + SOFT_BREAK_EVERY));
              }
              // Zero-width space allows splitTextToSize to break
              return parts.join('\u200b');
            })
            .join('');
        }
        
        // Detect decorative/filler lines like "-----" or "_____" or long dot runs
        isFillerString(text) {
          if (!text) return true;
          const compact = text.toString().replace(/[\s\u200b]+/g, '');
          if (compact.length < 3) return false;
          const filler = compact.match(/[-_–—.=]{3,}/g);
          if (!filler) return false;
          const fillerLen = filler.join('').length;
          return fillerLen / compact.length >= 0.7;
        }
        
        // Check if we need a new page
        checkPageBreak(requiredHeight = 20) {
          if (this.yPosition + requiredHeight > this.pageHeight) {
            this.pdf.addPage();
            this.yPosition = 20;
          }
        }
        
        // Set font properties
        setFont(size = 12, style = 'normal', font = 'helvetica') {
          try {
            this.pdf.setFont(font, style);
            this.pdf.setFontSize(size);
            this.currentFontSize = size;
          } catch (error) {
            console.warn('Font setting error:', error);
            // Fallback to default font
            this.pdf.setFont('helvetica', 'normal');
            this.pdf.setFontSize(size);
          }
        }
        
        // Add text with word wrapping and error handling
        addText(text, indent = 0, maxWidth = null) {
          if (!text || !text.trim()) return;
          
          try {
            const effectiveWidth = maxWidth || (this.maxWidth - indent);
            const textStr = this.normalizeToAscii(text.toString());
            // Preserve explicit newlines by splitting before wrapping
            const hardLines = textStr.split(/\r?\n/);
            for (const hardLine of hardLines) {
              const wrapped = this.pdf.splitTextToSize(hardLine, effectiveWidth);
              for (let i = 0; i < wrapped.length; i++) {
                this.checkPageBreak(10);
                this.pdf.text(wrapped[i], this.margin + indent, this.yPosition);
                this.yPosition += this.lineHeight;
              }
            }
          } catch (error) {
            console.warn('Text rendering error:', error);
            // Fallback: add simple text
            this.checkPageBreak(10);
            this.pdf.text(this.normalizeToAscii(text.toString()).substring(0, 100), this.margin + indent, this.yPosition);
            this.yPosition += this.lineHeight;
          }
        }
        
        // Add spacing
        addSpacing(multiplier = 1) {
          this.yPosition += (this.lineHeight * multiplier);
        }
        
        // Process inline markdown formatting with better error handling
        processInlineFormatting(text) {
          if (!text) return '';
          
          try {
            // Convert to string if not already
            text = this.normalizeToAscii(text.toString());
            
            // Handle bold text - remove ** but keep the text
            text = text.replace(/\*{2}(.*?)\*{2}/g, '$1');
            // Handle bold with underscores
            text = text.replace(/__([^_]+)__/g, '$1');
            
            // Handle italic text - remove * but keep the text
            text = text.replace(/\*([^*]+)\*/g, '$1');
            // Handle italic with underscores
            text = text.replace(/_([^_]+)_/g, '$1');
            
            // Handle inline code - remove ` but keep the text
            text = text.replace(/`([^`]+)`/g, '$1');
            
            // Handle links - keep only the link text
            text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
            
            // Handle strikethrough
            text = text.replace(/~~(.*?)~~/g, '$1');
            // Allow breaking very long tokens
            return this.softWrapLongWords(text.trim());
          } catch (error) {
            console.warn('Inline formatting error:', error);
            return this.softWrapLongWords(text.toString().trim());
          }
        }
        
        // Parse and render tables with improved error handling and layout
        renderTable(tableLines) {
          try {
            if (!tableLines || tableLines.length < 2) return;
            // Filter out empty lines and separator lines
            const validLines = tableLines.filter(line => 
              line.trim() &&
              line.includes('|') &&
              !line.match(/^\s*\|?[\s\-:]+\|?\s*$/)
            );
            if (validLines.length === 0) return;
            // Parse rows to cells (support optional edge pipes)
            const parsedRows = validLines.map((line) => {
              const t = line.trim();
              const parts = line.split('|');
              if (t.startsWith('|')) parts.shift();
              if (t.endsWith('|')) parts.pop();
              return parts.map(cell => this.processInlineFormatting(cell.trim()));
            });
            const headerCells = parsedRows[0] || [];
            let dataRows = parsedRows.slice(1);
            // Remove rows that are composed primarily of dashes/underscores (placeholders)
            const isDashOnly = (text) => {
              if (!text) return true;
              const t = (text || '').toString();
              const compact = t.replace(/\s+/g, '');
              if (compact.length === 0) return true;
              // If 70%+ of non-space chars are line/filler chars, treat as placeholder
              const fillerMatches = compact.match(/[-_–—.]/g) || [];
              return fillerMatches.length / compact.length >= 0.7;
            };
            if (headerCells.length > 0) {
              const threshold = Math.max(2, Math.ceil(headerCells.length * 0.6));
              dataRows = dataRows.filter(cells => {
                const dashCount = cells.reduce((acc, c) => acc + (isDashOnly(c) ? 1 : 0), 0);
                if (dashCount >= threshold) return false;
                const rowJoin = (cells.join(' ') || '').replace(/\s+/g, '');
                if (rowJoin && (rowJoin.match(/[-_–—.]/g) || []).length / rowJoin.length >= 0.7) {
                  return false;
                }
                return true;
              });
            }
            const numCols = headerCells.length;
            if (numCols === 0) return;
            // Allocate column widths by content weight
            const availableWidth = this.maxWidth - 10; // inner padding for table
            const weights = new Array(numCols).fill(0);
            const considerRows = [headerCells, ...dataRows];
            for (const row of considerRows) {
              for (let c = 0; c < numCols; c++) {
                const text = (row[c] || '').toString();
                weights[c] = Math.max(weights[c], Math.min(text.length, 60));
              }
            }
            const totalWeight = weights.reduce((s, w) => s + Math.max(w, 8), 0);
            const colWidths = weights.map(w => Math.max((Math.max(w, 8) / totalWeight) * availableWidth, 25));
            const cellPaddingX = 3;
            const rowMinHeight = 14;
            const drawHeader = () => {
              // Compute header height
              const headerHeights = headerCells.map((text, idx) => {
                const lines = this.pdf.splitTextToSize(text || '', colWidths[idx] - (cellPaddingX * 2));
                return Math.max(lines.length * 6 + 6, rowMinHeight);
              });
              const headerHeight = Math.max(...headerHeights);
              // Ensure space, otherwise new page
              if (this.yPosition + headerHeight > this.pageHeight) {
                this.pdf.addPage();
                this.yPosition = this.margin;
              }
              // Draw header row
              let x = this.margin + 5;
              const y = this.yPosition;
              for (let c = 0; c < numCols; c++) {
                this.pdf.setDrawColor(200, 200, 200);
                this.pdf.setLineWidth(0.5);
                this.pdf.setFillColor(245, 245, 245);
                this.pdf.rect(x, y, colWidths[c], headerHeight, 'FD');
                this.setFont(10, 'bold');
                this.pdf.setTextColor(0, 0, 0);
                const lines = this.pdf.splitTextToSize(headerCells[c] || '', colWidths[c] - (cellPaddingX * 2));
                let ty = y + 8;
                for (const ln of lines) {
                  this.pdf.text(ln, x + cellPaddingX, ty);
                  ty += 6;
                }
                x += colWidths[c];
              }
              this.yPosition += headerHeight;
            };
            const drawDataRow = (cells) => {
              // Compute row height
              const heights = cells.map((text, idx) => {
                const lines = this.pdf.splitTextToSize(text || '', colWidths[idx] - (cellPaddingX * 2));
                return Math.max(lines.length * 6 + 6, rowMinHeight);
              });
              const rowHeight = Math.max(...heights);
              // Page break with header repeat
              if (this.yPosition + rowHeight > this.pageHeight) {
                this.pdf.addPage();
                this.yPosition = this.margin;
                drawHeader();
              }
              let x = this.margin + 5;
              const y = this.yPosition;
              for (let c = 0; c < numCols; c++) {
                this.pdf.setDrawColor(200, 200, 200);
                this.pdf.setLineWidth(0.5);
                // Stroke only for data cells to avoid black fill in some viewers
                this.pdf.rect(x, y, colWidths[c], rowHeight, 'S');
                this.setFont(10, 'normal');
                this.pdf.setTextColor(0, 0, 0);
                const lines = this.pdf.splitTextToSize(cells[c] || '', colWidths[c] - (cellPaddingX * 2));
                let ty = y + 8;
                for (const ln of lines) {
                  if (ty > y + rowHeight - 2) break;
                  this.pdf.text(ln, x + cellPaddingX, ty);
                  ty += 6;
                }
                x += colWidths[c];
              }
              this.yPosition += rowHeight;
            };
            // Draw table: header first, then rows
            drawHeader();
            for (const row of dataRows) {
              // Pad row to numCols to avoid undefined access
              const cells = Array.from({ length: numCols }, (_, i) => row[i] || '');
              drawDataRow(cells);
            }
            this.addSpacing(2);
            this.setFont(12, 'normal');
            this.pdf.setTextColor(0, 0, 0);
          } catch (error) {
            console.warn('Table rendering error:', error);
            this.addText('Table content could not be rendered properly');
            this.addSpacing(1);
          }
        }
        
        // Enhanced list rendering with error handling
        renderList(content) {
          try {
            const lines = content.split('\n');
            
            for (const line of lines) {
              if (!line.trim()) continue;
              
              // Detect list type and indentation
              const bulletMatch = line.match(/^(\s*)[•*+-]\s+(.*)$/);
              const numberedMatch = line.match(/^(\s*)(\d+)\.\s+(.*)$/);
              
              if (bulletMatch) {
                const indent = bulletMatch[1].length;
                const text = this.processInlineFormatting(bulletMatch[2]);
                if (this.isFillerString(text)) continue;
                const startX = this.margin + indent * 5;
                const availableWidth = this.maxWidth - (indent * 5);
                const wrapped = this.pdf.splitTextToSize(`- ${text}`, availableWidth);
                for (let i = 0; i < wrapped.length; i++) {
                  this.checkPageBreak(10);
                  this.pdf.text(wrapped[i], startX, this.yPosition);
                  this.yPosition += this.lineHeight + 1;
                }
              } else if (numberedMatch) {
                const indent = numberedMatch[1].length;
                const num = numberedMatch[2];
                const text = this.processInlineFormatting(numberedMatch[3]);
                if (this.isFillerString(text)) continue;
                const startX = this.margin + indent * 5;
                const availableWidth = this.maxWidth - (indent * 5);
                const wrapped = this.pdf.splitTextToSize(`${num}. ${text}`, availableWidth);
                for (let i = 0; i < wrapped.length; i++) {
                  this.checkPageBreak(10);
                  this.pdf.text(wrapped[i], startX, this.yPosition);
                  this.yPosition += this.lineHeight + 1;
                }
              } else if (line.trim().startsWith('•')) {
                // Handle already formatted bullet points
                const text = this.processInlineFormatting(line.trim()).replace(/^•\s*/, '- ');
                if (this.isFillerString(text)) continue;
                const startX = this.margin;
                const wrapped = this.pdf.splitTextToSize(text, this.maxWidth);
                for (let i = 0; i < wrapped.length; i++) {
                  this.checkPageBreak(10);
                  this.pdf.text(wrapped[i], startX, this.yPosition);
                  this.yPosition += this.lineHeight + 1;
                }
              }
            }
            
            this.addSpacing(1);
          } catch (error) {
            console.warn('List rendering error:', error);
            this.addText('List content could not be rendered properly');
            this.addSpacing(1);
          }
        }
        
        // Main parsing method with comprehensive error handling
        parseMarkdown(markdown) {
          if (!markdown) return;
          
          try {
            const lines = markdown.split('\n');
            let i = 0;
            
            while (i < lines.length) {
              const line = lines[i].trim();
              
              // Skip empty lines
              if (!line) {
                i++;
                continue;
              }
              
              // Headers
              if (line.match(/^#{1,6}\s/)) {
                const level = (line.match(/^(#+)/) || ['', ''])[1].length;
                const text = line.replace(/^#+\s*/, '');
                
                this.addSpacing(level === 1 ? 2 : 1);
                
                if (level === 1) {
                  this.setFont(18, 'bold');
                } else if (level === 2) {
                  this.setFont(16, 'bold');
                } else if (level === 3) {
                  this.setFont(14, 'bold');
                } else {
                  this.setFont(12, 'bold');
                }
                
                this.addText(this.processInlineFormatting(text));
                this.addSpacing(0.5);
                this.setFont(12, 'normal');
                i++;
                continue;
              }
              
              // Tables - collect all table lines
              if (line.includes('|')) {
                const tableLines = [];
                while (i < lines.length && (lines[i].includes('|') || lines[i].match(/^\s*\|?[\s\-:]+\|?\s*$/))) {
                  if (lines[i].trim()) {
                    tableLines.push(lines[i]);
                  }
                  i++;
                }
                this.renderTable(tableLines);
                continue;
              }
              
              // Lists
            if (line.match(/^(\s*)[•*-]\s/) || line.match(/^(\s*)\d+\.\s/)) {
              const listLines = [];
              while (i < lines.length && 
                     (lines[i].match(/^(\s*)[•*-]\s/) || 
                      lines[i].match(/^(\s*)\d+\.\s/) || 
                      lines[i].trim().startsWith('•'))) {
                  listLines.push(lines[i]);
                  i++;
                }
                this.renderList(listLines.join('\n'));
                continue;
              }
              
              // Blockquotes
              if (line.startsWith('>')) {
                this.pdf.setTextColor(100, 100, 100);
                this.setFont(11, 'italic');
                this.addText(this.processInlineFormatting(line.substring(1).trim()), 10);
                this.pdf.setTextColor(0, 0, 0);
                this.setFont(12, 'normal');
                this.addSpacing(1);
                i++;
                continue;
              }
              
              // Horizontal rule
              if (line.match(/^[-*_]{3,}$/)) {
                // Skip rendering decorative rules to avoid unwanted dashed lines
                this.addSpacing(0.5);
                i++;
                continue;
              }
              
              // Regular paragraphs
              let paragraphLines = [line];
              i++;
              
              // Collect continuation lines for paragraph
              while (i < lines.length && 
                     lines[i].trim() && 
                     !lines[i].match(/^#{1,6}\s/) &&
                     !lines[i].includes('|') &&
                     !lines[i].match(/^(\s*)[•*-]\s/) &&
                     !lines[i].match(/^(\s*)\d+\.\s/) &&
                     !lines[i].startsWith('>') &&
                     !lines[i].match(/^[-*_]{3,}$/)) {
                paragraphLines.push(lines[i].trim());
                i++;
              }
              
              // Preserve single newlines within a paragraph for markdown-like soft breaks
              const paragraphText = paragraphLines.join('\n');
              if (this.isFillerString(paragraphText)) {
                // Ignore decorative filler paragraphs
                this.addSpacing(0.5);
                continue;
              }
              const processed = this.softWrapLongWords(this.processInlineFormatting(paragraphText));
              this.addText(processed);
              this.addSpacing(1);
            }
          } catch (error) {
            console.error('Markdown parsing error:', error);
            // Fallback: render as plain text
            this.addText('Content could not be parsed properly. Showing raw text:');
            this.addSpacing(1);
            this.addText(markdown.toString().substring(0, 500) + '...');
          }
        }
      }
      
      // Initialize PDF with proper settings
      pdf.setFont('helvetica', 'normal');
      
      // Add title with error handling
      try {
        pdf.setFontSize(20);
        pdf.setFont('helvetica', 'bold');
        pdf.text(asset.asset_name || 'Document', 20, 30);
      } catch (error) {
        console.warn('Title rendering error:', error);
        pdf.setFontSize(16);
        pdf.text('Document', 20, 30);
      }
      
      // Add metadata section with validation
      pdf.setFontSize(11);
      pdf.setFont('helvetica', 'normal');
      pdf.setTextColor(80, 80, 80);
      
      let metaY = 45;
      if (asset.asset_type) {
        pdf.text(`Type: ${asset.asset_type}`, 20, metaY);
        metaY += 7;
      }
      if (asset.asset_category) {
        pdf.text(`Category: ${asset.asset_category}`, 20, metaY);
        metaY += 7;
      }
      if (asset.asset_last_updated_by) {
        pdf.text(`Updated by: ${asset.asset_last_updated_by}`, 20, metaY);
        metaY += 7;
      }
      if (asset.asset_last_updated_at) {
        try {
          const date = new Date(asset.asset_last_updated_at);
          pdf.text(`Last updated: ${date.toLocaleString()}`, 20, metaY);
        } catch (error) {
          pdf.text(`Last updated: ${asset.asset_last_updated_at}`, 20, metaY);
        }
        metaY += 7;
      }
      
      // Reset color for content
      pdf.setTextColor(0, 0, 0);
      pdf.setFontSize(12);
      
      // Parse and render markdown content
      const parser = new MarkdownToPDF(pdf);
      parser.yPosition = Math.max(80, metaY + 10);
      parser.parseMarkdown(parser.normalizeToAscii(asset.asset_content));
      
      // Add footer to all pages with error handling
      try {
        const pageCount = pdf.internal.getNumberOfPages();
        const currentDate = new Date().toLocaleString();
        
        for (let pageNum = 1; pageNum <= pageCount; pageNum++) {
          pdf.setPage(pageNum);
          pdf.setFontSize(9);
          pdf.setTextColor(120, 120, 120);
          pdf.text(`Generated on ${currentDate}`, 20, 285);
          if (pageCount > 1) {
            pdf.text(`Page ${pageNum} of ${pageCount}`, 150, 285);
          }
        }
      } catch (error) {
        console.warn('Footer rendering error:', error);
      }
      
      // Save the PDF with sanitized filename
      const sanitizedName = assetName.replace(/[^a-zA-Z0-9-_]/g, '_');
      pdf.save(`${sanitizedName}.pdf`);
      
      return res.data;
      
    } catch (error) {
      console.error('PDF generation error:', error);
      throw new Error(`Failed to generate PDF: ${error.message}`);
    }
  },
  // Generate a PDF from raw markdown/text content with the same styling
  downloadContentAsPdf: async (title, content, meta = {}) => {
    try {
      const pdf = new jsPDF();

      class MarkdownToPDF {
        constructor(pdf) {
          this.pdf = pdf;
          this.margin = 20;
          const pageWidth = this.pdf.internal.pageSize.getWidth();
          const pageHeight = this.pdf.internal.pageSize.getHeight();
          this.pageWidth = pageWidth;
          this.pageHeight = pageHeight - 20;
          this.maxWidth = pageWidth - (this.margin * 2);
          this.yPosition = Math.max(80, this.margin);
          this.lineHeight = 6;
          this.currentFontSize = 12;
        }
        normalizeToAscii(text) {
          if (text == null) return '';
          return text
            .toString()
            .replace(/[\u2018\u2019]/g, "'")
            .replace(/[\u201C\u201D]/g, '"')
            .replace(/[\u2013\u2014]/g, '-')
            .replace(/[\u2022\u00B7]/g, '-')
            .replace(/[\u2026]/g, '...')
            .replace(/[\u00A0\u202F\u2009]/g, ' ')
            .replace(/[\u200B]/g, '');
        }
        softWrapLongWords(text) {
          if (!text) return '';
          const SOFT_BREAK_EVERY = 18;
          return text
            .split(/(\s+)/)
            .map(token => {
              if (/\s+/.test(token)) return token;
              if (token.length <= SOFT_BREAK_EVERY) return token;
              const parts = [];
              for (let i = 0; i < token.length; i += SOFT_BREAK_EVERY) {
                parts.push(token.slice(i, i + SOFT_BREAK_EVERY));
              }
              return parts.join('\u200b');
            })
            .join('');
        }
        isFillerString(text) {
          if (!text) return true;
          const compact = text.toString().replace(/[\s\u200b]+/g, '');
          if (compact.length < 3) return false;
          const filler = compact.match(/[-_–—.=]{3,}/g);
          if (!filler) return false;
          const fillerLen = filler.join('').length;
          return fillerLen / compact.length >= 0.7;
        }
        checkPageBreak(requiredHeight = 20) {
          if (this.yPosition + requiredHeight > this.pageHeight) {
            this.pdf.addPage();
            this.yPosition = 20;
          }
        }
        setFont(size = 12, style = 'normal', font = 'helvetica') {
          try {
            this.pdf.setFont(font, style);
            this.pdf.setFontSize(size);
            this.currentFontSize = size;
          } catch (error) {
            this.pdf.setFont('helvetica', 'normal');
            this.pdf.setFontSize(size);
          }
        }
        addText(text, indent = 0, maxWidth = null) {
          if (!text || !text.trim()) return;
          try {
            const effectiveWidth = maxWidth || (this.maxWidth - indent);
            const textStr = this.normalizeToAscii(text.toString());
            const hardLines = textStr.split(/\r?\n/);
            for (const hardLine of hardLines) {
              const wrapped = this.pdf.splitTextToSize(hardLine, effectiveWidth);
              for (let i = 0; i < wrapped.length; i++) {
                this.checkPageBreak(10);
                this.pdf.text(wrapped[i], this.margin + indent, this.yPosition);
                this.yPosition += this.lineHeight;
              }
            }
          } catch (error) {
            this.checkPageBreak(10);
            this.pdf.text(this.normalizeToAscii(text.toString()).substring(0, 100), this.margin + indent, this.yPosition);
            this.yPosition += this.lineHeight;
          }
        }
        addSpacing(multiplier = 1) {
          this.yPosition += (this.lineHeight * multiplier);
        }
        processInlineFormatting(text) {
          if (!text) return '';
          try {
            text = this.normalizeToAscii(text.toString());
            text = text.replace(/\*{2}(.*?)\*{2}/g, '$1');
            text = text.replace(/__([^_]+)__/g, '$1');
            text = text.replace(/\*([^*]+)\*/g, '$1');
            text = text.replace(/_([^_]+)_/g, '$1');
            text = text.replace(/`([^`]+)`/g, '$1');
            text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
            text = text.replace(/~~(.*?)~~/g, '$1');
            return this.softWrapLongWords(text.trim());
          } catch (error) {
            return this.softWrapLongWords(text.toString().trim());
          }
        }
        renderTable(tableLines) {
          try {
            if (!tableLines || tableLines.length < 2) return;
            const validLines = tableLines.filter(line => 
              line.trim() &&
              line.includes('|') &&
              !line.match(/^\s*\|?[\s\-:]+\|?\s*$/)
            );
            if (validLines.length === 0) return;
            const parsedRows = validLines.map((line) => {
              const t = line.trim();
              const parts = line.split('|');
              if (t.startsWith('|')) parts.shift();
              if (t.endsWith('|')) parts.pop();
              return parts.map(cell => this.processInlineFormatting(cell.trim()));
            });
            const headerCells = parsedRows[0] || [];
            let dataRows = parsedRows.slice(1);
            const isDashOnly = (text) => {
              if (!text) return true;
              const t = (text || '').toString();
              const compact = t.replace(/\s+/g, '');
              if (compact.length === 0) return true;
              const fillerMatches = compact.match(/[-_–—.]/g) || [];
              return fillerMatches.length / compact.length >= 0.7;
            };
            if (headerCells.length > 0) {
              const threshold = Math.max(2, Math.ceil(headerCells.length * 0.6));
              dataRows = dataRows.filter(cells => {
                const dashCount = cells.reduce((acc, c) => acc + (isDashOnly(c) ? 1 : 0), 0);
                if (dashCount >= threshold) return false;
                const rowJoin = (cells.join(' ') || '').replace(/\s+/g, '');
                if (rowJoin && (rowJoin.match(/[-_–—.]/g) || []).length / rowJoin.length >= 0.7) {
                  return false;
                }
                return true;
              });
            }
            const numCols = headerCells.length;
            if (numCols === 0) return;
            const availableWidth = this.maxWidth - 10;
            const weights = new Array(numCols).fill(0);
            const considerRows = [headerCells, ...dataRows];
            for (const row of considerRows) {
              for (let c = 0; c < numCols; c++) {
                const text = (row[c] || '').toString();
                weights[c] = Math.max(weights[c], Math.min(text.length, 60));
              }
            }
            const totalWeight = weights.reduce((s, w) => s + Math.max(w, 8), 0);
            const colWidths = weights.map(w => Math.max((Math.max(w, 8) / totalWeight) * availableWidth, 25));
            const cellPaddingX = 3;
            const rowMinHeight = 14;
            const drawHeader = () => {
              const headerHeights = headerCells.map((text, idx) => {
                const lines = this.pdf.splitTextToSize(text || '', colWidths[idx] - (cellPaddingX * 2));
                return Math.max(lines.length * 6 + 6, rowMinHeight);
              });
              const headerHeight = Math.max(...headerHeights);
              if (this.yPosition + headerHeight > this.pageHeight) {
                this.pdf.addPage();
                this.yPosition = this.margin;
              }
              let x = this.margin + 5;
              const y = this.yPosition;
              for (let c = 0; c < numCols; c++) {
                this.pdf.setDrawColor(200, 200, 200);
                this.pdf.setLineWidth(0.5);
                this.pdf.setFillColor(245, 245, 245);
                this.pdf.rect(x, y, colWidths[c], headerHeight, 'FD');
                this.setFont(10, 'bold');
                this.pdf.setTextColor(0, 0, 0);
                const lines = this.pdf.splitTextToSize(headerCells[c] || '', colWidths[c] - (cellPaddingX * 2));
                let ty = y + 8;
                for (const ln of lines) {
                  this.pdf.text(ln, x + cellPaddingX, ty);
                  ty += 6;
                }
                x += colWidths[c];
              }
              this.yPosition += headerHeight;
            };
            const drawDataRow = (cells) => {
              const heights = cells.map((text, idx) => {
                const lines = this.pdf.splitTextToSize(text || '', colWidths[idx] - (cellPaddingX * 2));
                return Math.max(lines.length * 6 + 6, rowMinHeight);
              });
              const rowHeight = Math.max(...heights);
              if (this.yPosition + rowHeight > this.pageHeight) {
                this.pdf.addPage();
                this.yPosition = this.margin;
                drawHeader();
              }
              let x = this.margin + 5;
              const y = this.yPosition;
              for (let c = 0; c < numCols; c++) {
                this.pdf.setDrawColor(200, 200, 200);
                this.pdf.setLineWidth(0.5);
                this.pdf.rect(x, y, colWidths[c], rowHeight, 'S');
                this.setFont(10, 'normal');
                this.pdf.setTextColor(0, 0, 0);
                const lines = this.pdf.splitTextToSize(cells[c] || '', colWidths[c] - (cellPaddingX * 2));
                let ty = y + 8;
                for (const ln of lines) {
                  if (ty > y + rowHeight - 2) break;
                  this.pdf.text(ln, x + cellPaddingX, ty);
                  ty += 6;
                }
                x += colWidths[c];
              }
              this.yPosition += rowHeight;
            };
            drawHeader();
            for (const row of dataRows) {
              const cells = Array.from({ length: numCols }, (_, i) => row[i] || '');
              drawDataRow(cells);
            }
            this.addSpacing(2);
            this.setFont(12, 'normal');
            this.pdf.setTextColor(0, 0, 0);
          } catch (error) {
            this.addText('Table content could not be rendered properly');
            this.addSpacing(1);
          }
        }
        renderList(content) {
          try {
            const lines = content.split('\n');
            for (const line of lines) {
              if (!line.trim()) continue;
              const bulletMatch = line.match(/^(\s*)[•*+-]\s+(.*)$/);
              const numberedMatch = line.match(/^(\s*)(\d+)\.\s+(.*)$/);
              if (bulletMatch) {
                const indent = bulletMatch[1].length;
                const text = this.processInlineFormatting(bulletMatch[2]);
                if (this.isFillerString(text)) continue;
                const startX = this.margin + indent * 5;
                const availableWidth = this.maxWidth - (indent * 5);
                const wrapped = this.pdf.splitTextToSize(`- ${text}`, availableWidth);
                for (let i = 0; i < wrapped.length; i++) {
                  this.checkPageBreak(10);
                  this.pdf.text(wrapped[i], startX, this.yPosition);
                  this.yPosition += this.lineHeight + 1;
                }
              } else if (numberedMatch) {
                const indent = numberedMatch[1].length;
                const num = numberedMatch[2];
                const text = this.processInlineFormatting(numberedMatch[3]);
                if (this.isFillerString(text)) continue;
                const startX = this.margin + indent * 5;
                const availableWidth = this.maxWidth - (indent * 5);
                const wrapped = this.pdf.splitTextToSize(`${num}. ${text}`, availableWidth);
                for (let i = 0; i < wrapped.length; i++) {
                  this.checkPageBreak(10);
                  this.pdf.text(wrapped[i], startX, this.yPosition);
                  this.yPosition += this.lineHeight + 1;
                }
              } else if (line.trim().startsWith('•')) {
                const text = this.processInlineFormatting(line.trim()).replace(/^•\s*/, '- ');
                if (this.isFillerString(text)) continue;
                const startX = this.margin;
                const wrapped = this.pdf.splitTextToSize(text, this.maxWidth);
                for (let i = 0; i < wrapped.length; i++) {
                  this.checkPageBreak(10);
                  this.pdf.text(wrapped[i], startX, this.yPosition);
                  this.yPosition += this.lineHeight + 1;
                }
              }
            }
            this.addSpacing(1);
          } catch (error) {
            this.addText('List content could not be rendered properly');
            this.addSpacing(1);
          }
        }
        parseMarkdown(markdown) {
          if (!markdown) return;
          try {
            const lines = markdown.split('\n');
            let i = 0;
            while (i < lines.length) {
              const line = lines[i].trim();
              if (!line) { i++; continue; }
              if (line.match(/^#{1,6}\s/)) {
                const level = (line.match(/^(#+)/) || ['', ''])[1].length;
                const text = line.replace(/^#+\s*/, '');
                this.addSpacing(level === 1 ? 2 : 1);
                if (level === 1) { this.setFont(18, 'bold'); }
                else if (level === 2) { this.setFont(16, 'bold'); }
                else if (level === 3) { this.setFont(14, 'bold'); }
                else { this.setFont(12, 'bold'); }
                this.addText(this.processInlineFormatting(text));
                this.addSpacing(0.5);
                this.setFont(12, 'normal');
                i++;
                continue;
              }
              if (line.includes('|')) {
                const tableLines = [];
                while (i < lines.length && (lines[i].includes('|') || lines[i].match(/^\s*\|?[\s\-:]+\|?\s*$/))) {
                  if (lines[i].trim()) { tableLines.push(lines[i]); }
                  i++;
                }
                this.renderTable(tableLines);
                continue;
              }
              if (line.match(/^(\s*)[•*-]\s/) || line.match(/^(\s*)\d+\.\s/)) {
                const listLines = [];
                while (i < lines.length && (lines[i].match(/^(\s*)[•*-]\s/) || lines[i].match(/^(\s*)\d+\.\s/) || lines[i].trim().startsWith('•'))) {
                  listLines.push(lines[i]);
                  i++;
                }
                this.renderList(listLines.join('\n'));
                continue;
              }
              if (line.startsWith('>')) {
                this.pdf.setTextColor(100, 100, 100);
                this.setFont(11, 'italic');
                this.addText(this.processInlineFormatting(line.substring(1).trim()), 10);
                this.pdf.setTextColor(0, 0, 0);
                this.setFont(12, 'normal');
                this.addSpacing(1);
                i++;
                continue;
              }
              if (line.match(/^[-*_]{3,}$/)) {
                this.addSpacing(0.5);
                i++;
                continue;
              }
              let paragraphLines = [line];
              i++;
              while (i < lines.length && lines[i].trim() && !lines[i].match(/^#{1,6}\s/) && !lines[i].includes('|') && !lines[i].match(/^(\s*)[•*-]\s/) && !lines[i].match(/^(\s*)\d+\.\s/) && !lines[i].startsWith('>') && !lines[i].match(/^[-*_]{3,}$/)) {
                paragraphLines.push(lines[i].trim());
                i++;
              }
              const paragraphText = paragraphLines.join('\n');
              if (this.isFillerString(paragraphText)) { this.addSpacing(0.5); continue; }
              const processed = this.softWrapLongWords(this.processInlineFormatting(paragraphText));
              this.addText(processed);
              this.addSpacing(1);
            }
          } catch (error) {
            this.addText('Content could not be parsed properly. Showing raw text:');
            this.addSpacing(1);
            this.addText(markdown.toString().substring(0, 500) + '...');
          }
        }
      }

      pdf.setFont('helvetica', 'normal');
      try {
        pdf.setFontSize(20);
        pdf.setFont('helvetica', 'bold');
        pdf.text((title || 'Document'), 20, 30);
      } catch (error) {
        pdf.setFontSize(16);
        pdf.text('Document', 20, 30);
      }

      pdf.setFontSize(11);
      pdf.setFont('helvetica', 'normal');
      pdf.setTextColor(80, 80, 80);

      let metaY = 45;
      if (meta.asset_type) { pdf.text(`Type: ${meta.asset_type}`, 20, metaY); metaY += 7; }
      if (meta.asset_category) { pdf.text(`Category: ${meta.asset_category}`, 20, metaY); metaY += 7; }
      if (meta.updated_by) { pdf.text(`Updated by: ${meta.updated_by}`, 20, metaY); metaY += 7; }
      if (meta.updated_at) {
        try { const date = new Date(meta.updated_at); pdf.text(`Last updated: ${date.toLocaleString()}`, 20, metaY); }
        catch { pdf.text(`Last updated: ${meta.updated_at}`, 20, metaY); }
        metaY += 7;
      }

      pdf.setTextColor(0, 0, 0);
      pdf.setFontSize(12);

      const parser = new MarkdownToPDF(pdf);
      parser.yPosition = Math.max(80, metaY + 10);
      parser.parseMarkdown(parser.normalizeToAscii(content || ''));

      try {
        const pageCount = pdf.internal.getNumberOfPages();
        const currentDate = new Date().toLocaleString();
        for (let pageNum = 1; pageNum <= pageCount; pageNum++) {
          pdf.setPage(pageNum);
          pdf.setFontSize(9);
          pdf.setTextColor(120, 120, 120);
          pdf.text(`Generated on ${currentDate}`, 20, 285);
          if (pageCount > 1) {
            pdf.text(`Page ${pageNum} of ${pageCount}`, 150, 285);
          }
        }
      } catch {}

      const sanitizedName = (title || 'document').toString().replace(/[^a-zA-Z0-9-_]/g, '_');
      pdf.save(`${sanitizedName}.pdf`);
    } catch (error) {
      console.error('PDF generation error:', error);
      throw new Error(`Failed to generate PDF: ${error.message}`);
    }
  },
  // Generate a PDF Blob from raw markdown/text content with the same styling as downloadContentAsPdf
  generateContentPdfBlob: async (title, content, meta = {}) => {
    try {
      const pdf = new jsPDF();

      class MarkdownToPDF {
        constructor(pdf) {
          this.pdf = pdf;
          this.margin = 20;
          const pageWidth = this.pdf.internal.pageSize.getWidth();
          const pageHeight = this.pdf.internal.pageSize.getHeight();
          this.pageWidth = pageWidth;
          this.pageHeight = pageHeight - 20;
          this.maxWidth = pageWidth - (this.margin * 2);
          this.yPosition = Math.max(80, this.margin);
          this.lineHeight = 6;
          this.currentFontSize = 12;
        }
        normalizeToAscii(text) {
          if (text == null) return '';
          return text
            .toString()
            .replace(/[\u2018\u2019]/g, "'")
            .replace(/[\u201C\u201D]/g, '"')
            .replace(/[\u2013\u2014]/g, '-')
            .replace(/[\u2022\u00B7]/g, '-')
            .replace(/[\u2026]/g, '...')
            .replace(/[\u00A0\u202F\u2009]/g, ' ')
            .replace(/[\u200B]/g, '');
        }
        softWrapLongWords(text) {
          if (!text) return '';
          const SOFT_BREAK_EVERY = 18;
          return text
            .split(/(\s+)/)
            .map(token => {
              if (/\s+/.test(token)) return token;
              if (token.length <= SOFT_BREAK_EVERY) return token;
              const parts = [];
              for (let i = 0; i < token.length; i += SOFT_BREAK_EVERY) {
                parts.push(token.slice(i, i + SOFT_BREAK_EVERY));
              }
              return parts.join('\u200b');
            })
            .join('');
        }
        isFillerString(text) {
          if (!text) return true;
          const compact = text.toString().replace(/[\s\u200b]+/g, '');
          if (compact.length < 3) return false;
          const filler = compact.match(/[-_–—.=]{3,}/g);
          if (!filler) return false;
          const fillerLen = filler.join('').length;
          return fillerLen / compact.length >= 0.7;
        }
        checkPageBreak(requiredHeight = 20) {
          if (this.yPosition + requiredHeight > this.pageHeight) {
            this.pdf.addPage();
            this.yPosition = 20;
          }
        }
        setFont(size = 12, style = 'normal', font = 'helvetica') {
          try {
            this.pdf.setFont(font, style);
            this.pdf.setFontSize(size);
            this.currentFontSize = size;
          } catch (error) {
            this.pdf.setFont('helvetica', 'normal');
            this.pdf.setFontSize(size);
          }
        }
        addText(text, indent = 0, maxWidth = null) {
          if (!text || !text.trim()) return;
          try {
            const effectiveWidth = maxWidth || (this.maxWidth - indent);
            const textStr = this.normalizeToAscii(text.toString());
            const hardLines = textStr.split(/\r?\n/);
            for (const hardLine of hardLines) {
              const wrapped = this.pdf.splitTextToSize(hardLine, effectiveWidth);
              for (let i = 0; i < wrapped.length; i++) {
                this.checkPageBreak(10);
                this.pdf.text(wrapped[i], this.margin + indent, this.yPosition);
                this.yPosition += this.lineHeight;
              }
            }
          } catch (error) {
            this.checkPageBreak(10);
            this.pdf.text(this.normalizeToAscii(text.toString()).substring(0, 100), this.margin + indent, this.yPosition);
            this.yPosition += this.lineHeight;
          }
        }
        addSpacing(multiplier = 1) {
          this.yPosition += (this.lineHeight * multiplier);
        }
        processInlineFormatting(text) {
          if (!text) return '';
          try {
            text = this.normalizeToAscii(text.toString());
            text = text.replace(/\*{2}(.*?)\*{2}/g, '$1');
            text = text.replace(/__([^_]+)__/g, '$1');
            text = text.replace(/\*([^*]+)\*/g, '$1');
            text = text.replace(/_([^_]+)_/g, '$1');
            text = text.replace(/`([^`]+)`/g, '$1');
            text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
            text = text.replace(/~~(.*?)~~/g, '$1');
            return this.softWrapLongWords(text.trim());
          } catch (error) {
            return this.softWrapLongWords(text.toString().trim());
          }
        }
        renderTable(tableLines) {
          try {
            if (!tableLines || tableLines.length < 2) return;
            const validLines = tableLines.filter(line => 
              line.trim() &&
              line.includes('|') &&
              !line.match(/^\s*\|?[\s\-:]+\|?\s*$/)
            );
            if (validLines.length === 0) return;
            const parsedRows = validLines.map((line) => {
              const t = line.trim();
              const parts = line.split('|');
              if (t.startsWith('|')) parts.shift();
              if (t.endsWith('|')) parts.pop();
              return parts.map(cell => this.processInlineFormatting(cell.trim()));
            });
            const headerCells = parsedRows[0] || [];
            let dataRows = parsedRows.slice(1);
            const isDashOnly = (text) => {
              if (!text) return true;
              const t = (text || '').toString();
              const compact = t.replace(/\s+/g, '');
              if (compact.length === 0) return true;
              const fillerMatches = compact.match(/[-_–—.]/g) || [];
              return fillerMatches.length / compact.length >= 0.7;
            };
            if (headerCells.length > 0) {
              const threshold = Math.max(2, Math.ceil(headerCells.length * 0.6));
              dataRows = dataRows.filter(cells => {
                const dashCount = cells.reduce((acc, c) => acc + (isDashOnly(c) ? 1 : 0), 0);
                if (dashCount >= threshold) return false;
                const rowJoin = (cells.join(' ') || '').replace(/\s+/g, '');
                if (rowJoin && (rowJoin.match(/[-_–—.]/g) || []).length / rowJoin.length >= 0.7) {
                  return false;
                }
                return true;
              });
            }
            const numCols = headerCells.length;
            if (numCols === 0) return;
            const availableWidth = this.maxWidth - 10;
            const weights = new Array(numCols).fill(0);
            const considerRows = [headerCells, ...dataRows];
            for (const row of considerRows) {
              for (let c = 0; c < numCols; c++) {
                const text = (row[c] || '').toString();
                weights[c] = Math.max(weights[c], Math.min(text.length, 60));
              }
            }
            const totalWeight = weights.reduce((s, w) => s + Math.max(w, 8), 0);
            const colWidths = weights.map(w => Math.max((Math.max(w, 8) / totalWeight) * availableWidth, 25));
            const cellPaddingX = 3;
            const rowMinHeight = 14;
            const drawHeader = () => {
              const headerHeights = headerCells.map((text, idx) => {
                const lines = this.pdf.splitTextToSize(text || '', colWidths[idx] - (cellPaddingX * 2));
                return Math.max(lines.length * 6 + 6, rowMinHeight);
              });
              const headerHeight = Math.max(...headerHeights);
              if (this.yPosition + headerHeight > this.pageHeight) {
                this.pdf.addPage();
                this.yPosition = this.margin;
              }
              let x = this.margin + 5;
              const y = this.yPosition;
              for (let c = 0; c < numCols; c++) {
                this.pdf.setDrawColor(200, 200, 200);
                this.pdf.setLineWidth(0.5);
                this.pdf.setFillColor(245, 245, 245);
                this.pdf.rect(x, y, colWidths[c], headerHeight, 'FD');
                this.setFont(10, 'bold');
                this.pdf.setTextColor(0, 0, 0);
                const lines = this.pdf.splitTextToSize(headerCells[c] || '', colWidths[c] - (cellPaddingX * 2));
                let ty = y + 8;
                for (const ln of lines) {
                  this.pdf.text(ln, x + cellPaddingX, ty);
                  ty += 6;
                }
                x += colWidths[c];
              }
              this.yPosition += headerHeight;
            };
            const drawDataRow = (cells) => {
              const heights = cells.map((text, idx) => {
                const lines = this.pdf.splitTextToSize(text || '', colWidths[idx] - (cellPaddingX * 2));
                return Math.max(lines.length * 6 + 6, rowMinHeight);
              });
              const rowHeight = Math.max(...heights);
              if (this.yPosition + rowHeight > this.pageHeight) {
                this.pdf.addPage();
                this.yPosition = this.margin;
                drawHeader();
              }
              let x = this.margin + 5;
              const y = this.yPosition;
              for (let c = 0; c < numCols; c++) {
                this.pdf.setDrawColor(200, 200, 200);
                this.pdf.setLineWidth(0.5);
                this.pdf.rect(x, y, colWidths[c], rowHeight, 'S');
                this.setFont(10, 'normal');
                this.pdf.setTextColor(0, 0, 0);
                const lines = this.pdf.splitTextToSize(cells[c] || '', colWidths[c] - (cellPaddingX * 2));
                let ty = y + 8;
                for (const ln of lines) {
                  if (ty > y + rowHeight - 2) break;
                  this.pdf.text(ln, x + cellPaddingX, ty);
                  ty += 6;
                }
                x += colWidths[c];
              }
              this.yPosition += rowHeight;
            };
            drawHeader();
            for (const row of dataRows) {
              const cells = Array.from({ length: numCols }, (_, i) => row[i] || '');
              drawDataRow(cells);
            }
            this.addSpacing(2);
            this.setFont(12, 'normal');
            this.pdf.setTextColor(0, 0, 0);
          } catch (error) {
            this.addText('Table content could not be rendered properly');
            this.addSpacing(1);
          }
        }
        renderList(content) {
          try {
            const lines = content.split('\n');
            for (const line of lines) {
              if (!line.trim()) continue;
              const bulletMatch = line.match(/^(\s*)[•*+-]\s+(.*)$/);
              const numberedMatch = line.match(/^(\s*)(\d+)\.\s+(.*)$/);
              if (bulletMatch) {
                const indent = bulletMatch[1].length;
                const text = this.processInlineFormatting(bulletMatch[2]);
                if (this.isFillerString(text)) continue;
                const startX = this.margin + indent * 5;
                const availableWidth = this.maxWidth - (indent * 5);
                const wrapped = this.pdf.splitTextToSize(`- ${text}`, availableWidth);
                for (let i = 0; i < wrapped.length; i++) {
                  this.checkPageBreak(10);
                  this.pdf.text(wrapped[i], startX, this.yPosition);
                  this.yPosition += this.lineHeight + 1;
                }
              } else if (numberedMatch) {
                const indent = numberedMatch[1].length;
                const num = numberedMatch[2];
                const text = this.processInlineFormatting(numberedMatch[3]);
                if (this.isFillerString(text)) continue;
                const startX = this.margin + indent * 5;
                const availableWidth = this.maxWidth - (indent * 5);
                const wrapped = this.pdf.splitTextToSize(`${num}. ${text}`, availableWidth);
                for (let i = 0; i < wrapped.length; i++) {
                  this.checkPageBreak(10);
                  this.pdf.text(wrapped[i], startX, this.yPosition);
                  this.yPosition += this.lineHeight + 1;
                }
              } else if (line.trim().startsWith('•')) {
                const text = this.processInlineFormatting(line.trim()).replace(/^•\s*/, '- ');
                if (this.isFillerString(text)) continue;
                const startX = this.margin;
                const wrapped = this.pdf.splitTextToSize(text, this.maxWidth);
                for (let i = 0; i < wrapped.length; i++) {
                  this.checkPageBreak(10);
                  this.pdf.text(wrapped[i], startX, this.yPosition);
                  this.yPosition += this.lineHeight + 1;
                }
              }
            }
            this.addSpacing(1);
          } catch (error) {
            this.addText('List content could not be rendered properly');
            this.addSpacing(1);
          }
        }
        parseMarkdown(markdown) {
          if (!markdown) return;
          try {
            const lines = markdown.split('\n');
            let i = 0;
            while (i < lines.length) {
              const line = lines[i].trim();
              if (!line) { i++; continue; }
              if (line.match(/^#{1,6}\s/)) {
                const level = (line.match(/^(#+)/) || ['', ''])[1].length;
                const text = line.replace(/^#+\s*/, '');
                this.addSpacing(level === 1 ? 2 : 1);
                if (level === 1) { this.setFont(18, 'bold'); }
                else if (level === 2) { this.setFont(16, 'bold'); }
                else if (level === 3) { this.setFont(14, 'bold'); }
                else { this.setFont(12, 'bold'); }
                this.addText(this.processInlineFormatting(text));
                this.addSpacing(0.5);
                this.setFont(12, 'normal');
                i++;
                continue;
              }
              if (line.includes('|')) {
                const tableLines = [];
                while (i < lines.length && (lines[i].includes('|') || lines[i].match(/^\s*\|?[\s\-:]+\|?\s*$/))) {
                  if (lines[i].trim()) { tableLines.push(lines[i]); }
                  i++;
                }
                this.renderTable(tableLines);
                continue;
              }
              if (line.match(/^(\s*)[•*-]\s/) || line.match(/^(\s*)\d+\.\s/)) {
                const listLines = [];
                while (i < lines.length && (lines[i].match(/^(\s*)[•*-]\s/) || lines[i].match(/^(\s*)\d+\.\s/) || lines[i].trim().startsWith('•'))) {
                  listLines.push(lines[i]);
                  i++;
                }
                this.renderList(listLines.join('\n'));
                continue;
              }
              if (line.startsWith('>')) {
                this.pdf.setTextColor(100, 100, 100);
                this.setFont(11, 'italic');
                this.addText(this.processInlineFormatting(line.substring(1).trim()), 10);
                this.pdf.setTextColor(0, 0, 0);
                this.setFont(12, 'normal');
                this.addSpacing(1);
                i++;
                continue;
              }
              if (line.match(/^[-*_]{3,}$/)) {
                this.addSpacing(0.5);
                i++;
                continue;
              }
              let paragraphLines = [line];
              i++;
              while (i < lines.length && lines[i].trim() && !lines[i].match(/^#{1,6}\s/) && !lines[i].includes('|') && !lines[i].match(/^(\s*)[•*-]\s/) && !lines[i].match(/^(\s*)\d+\.\s/) && !lines[i].startsWith('>') && !lines[i].match(/^[-*_]{3,}$/)) {
                paragraphLines.push(lines[i].trim());
                i++;
              }
              const paragraphText = paragraphLines.join('\n');
              if (this.isFillerString(paragraphText)) { this.addSpacing(0.5); continue; }
              const processed = this.softWrapLongWords(this.processInlineFormatting(paragraphText));
              this.addText(processed);
              this.addSpacing(1);
            }
          } catch (error) {
            this.addText('Content could not be parsed properly. Showing raw text:');
            this.addSpacing(1);
            this.addText(markdown.toString().substring(0, 500) + '...');
          }
        }
      }

      pdf.setFont('helvetica', 'normal');
      try {
        pdf.setFontSize(20);
        pdf.setFont('helvetica', 'bold');
        pdf.text((title || 'Document'), 20, 30);
      } catch (error) {
        pdf.setFontSize(16);
        pdf.text('Document', 20, 30);
      }

      pdf.setFontSize(11);
      pdf.setFont('helvetica', 'normal');
      pdf.setTextColor(80, 80, 80);

      let metaY = 45;
      if (meta.asset_type) { pdf.text(`Type: ${meta.asset_type}`, 20, metaY); metaY += 7; }
      if (meta.asset_category) { pdf.text(`Category: ${meta.asset_category}`, 20, metaY); metaY += 7; }
      if (meta.updated_by) { pdf.text(`Updated by: ${meta.updated_by}`, 20, metaY); metaY += 7; }
      if (meta.updated_at) {
        try { const date = new Date(meta.updated_at); pdf.text(`Last updated: ${date.toLocaleString()}`, 20, metaY); }
        catch { pdf.text(`Last updated: ${meta.updated_at}`, 20, metaY); }
        metaY += 7;
      }

      pdf.setTextColor(0, 0, 0);
      pdf.setFontSize(12);

      const parser = new MarkdownToPDF(pdf);
      parser.yPosition = Math.max(80, metaY + 10);
      parser.parseMarkdown(parser.normalizeToAscii(content || ''));

      try {
        const pageCount = pdf.internal.getNumberOfPages();
        const currentDate = new Date().toLocaleString();
        for (let pageNum = 1; pageNum <= pageCount; pageNum++) {
          pdf.setPage(pageNum);
          pdf.setFontSize(9);
          pdf.setTextColor(120, 120, 120);
          pdf.text(`Generated on ${currentDate}`, 20, 285);
          if (pageCount > 1) {
            pdf.text(`Page ${pageNum} of ${pageCount}`, 150, 285);
          }
        }
      } catch {}

      const blob = pdf.output('blob');
      return blob;
    } catch (error) {
      console.error('PDF generation error:', error);
      throw new Error(`Failed to generate PDF: ${error.message}`);
    }
  },
  // Generate image for an asset type (e.g., concept-map)
  generateImageAsset: async (courseId, assetTypeName) => {
    try {
      const res = await axios.post(
        `${API_BASE}/courses/${courseId}/assets/image`,
        {},
        {
          headers: { 'Authorization': `Bearer ${getToken()}` },
          params: { asset_type_name: assetTypeName }
        }
      );
      return res.data; // expects { image_url }
    } catch (error) {
      handleAxiosError(error);
    }
  }
}; 