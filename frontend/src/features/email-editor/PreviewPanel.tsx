import React, { useEffect, useState } from 'react';
import { EmailDocument } from './types';

interface PreviewPanelProps {
  document: EmailDocument;
  mode: 'desktop' | 'mobile';
}

const PreviewPanel: React.FC<PreviewPanelProps> = ({ document, mode }) => {
  const [previewHtml, setPreviewHtml] = useState<string>('');

  // In a real implementation, this would call the backend API to render the document
  // For now, we'll simulate the rendering
  useEffect(() => {
    // This is a simplified simulation
    // In reality, this would make an API call to render the document to HTML
    const generatePreviewHtml = () => {
      return `
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>${document.metadata.subject}</title>
          <style>
            body {
              margin: 0;
              padding: 20px;
              background-color: ${document.settings.background_color};
              font-family: Arial, sans-serif;
            }
            .email-container {
              max-width: ${document.settings.width}px;
              margin: 0 auto;
              background-color: ${document.settings.content_background};
              border-radius: 8px;
              overflow: hidden;
              box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            .section {
              padding: 20px;
              border-bottom: 1px solid #eee;
            }
            .section:last-child {
              border-bottom: none;
            }
            h1, h2, h3, h4, h5, h6 {
              margin-top: 0;
            }
            img {
              max-width: 100%;
              height: auto;
            }
            .button {
              display: inline-block;
              padding: 12px 24px;
              text-decoration: none;
              border-radius: 4px;
              font-weight: bold;
            }
            .columns {
              display: flex;
              gap: 20px;
            }
            .column {
              flex: 1;
            }
            @media (max-width: 600px) {
              .columns {
                flex-direction: column;
              }
              .email-container {
                border-radius: 0;
              }
            }
          </style>
        </head>
        <body>
          <div class="email-container">
            <div class="section">
              <h1>${document.metadata.subject}</h1>
              ${document.metadata.preheader ? `<p>${document.metadata.preheader}</p>` : ''}
            </div>
            ${document.sections.map(section => `
              <div class="section">
                ${renderSectionPreview(section)}
              </div>
            `).join('')}
          </div>
        </body>
        </html>
      `;
    };

    const renderSectionPreview = (section: any) => {
      const { type, props } = section;
      
      switch (type) {
        case 'header':
          return `<h2>${props.text || 'Header Text'}</h2>`;
        
        case 'hero':
          return `
            <div style="text-align: ${props.alignment || 'center'};">
              <h1>${props.title || 'Hero Title'}</h1>
              ${props.subtitle ? `<p>${props.subtitle}</p>` : ''}
            </div>
          `;
        
        case 'heading':
          const level = props.level || 2;
          return `<h${level}>${props.text || 'Heading Text'}</h${level}>`;
        
        case 'paragraph':
          return `<p style="text-align: ${props.alignment || 'left'};">${props.content || 'Paragraph text...'}</p>`;
        
        case 'image':
          if (props.src) {
            return `<img src="${props.src}" alt="${props.alt || 'Image'}" style="width: ${props.width || '100%'};" />`;
          } else {
            return `<div style="background: #f0f0f0; padding: 20px; text-align: center;">[Image Placeholder]</div>`;
          }
        
        case 'button':
          return `
            <a href="${props.url || '#'}" class="button" style="
              background-color: ${props.background_color || '#007bff'};
              color: ${props.text_color || '#ffffff'};
              border-radius: ${props.border_radius || '4px'};
              display: inline-block;
            ">
              ${props.label || 'Button'}
            </a>
          `;
        
        case 'divider':
          return `<hr style="
            border-width: ${props.border_width || '1px'};
            border-style: ${props.border_style || 'solid'};
            border-color: ${props.border_color || '#cccccc'};
            margin: 20px 0;
          ">`;
        
        case 'spacer':
          return `<div style="height: ${props.height || '20px'};"></div>`;
        
        case 'columns':
          const columns = props.columns || [];
          return `
            <div class="columns">
              ${columns.map((col: any) => `
                <div class="column">
                  <p>Column content placeholder</p>
                </div>
              `).join('')}
            </div>
          `;
        
        case 'social':
          const links = props.links || [];
          return `
            <div>
              <p>Social Links (${links.length} platforms):</p>
              ${links.map((link: any) => `
                <a href="${link.url || '#'}">${link.platform || 'Link'}</a>
              `).join(' | ')}
            </div>
          `;
        
        case 'footer':
          return `<div style="text-align: center; padding: 20px; border-top: 1px solid #eee;">
            <p>${props.text || 'Footer text'}</p>
          </div>`;
        
        case 'html':
          return props.html || '<p>Custom HTML content</p>';
        
        default:
          return `<p>Unsupported section type: ${type}</p>`;
      }
    };

    setPreviewHtml(generatePreviewHtml());
  }, [document, mode]);

  return (
    <div className={`preview-panel ${mode}`}>
      <div className="preview-frame">
        <iframe
          srcDoc={previewHtml}
          title="Email Preview"
          sandbox="allow-scripts allow-same-origin"
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            transform: mode === 'mobile' ? 'scale(0.5)' : 'none',
            transformOrigin: '0 0'
          }}
        />
      </div>
    </div>
  );
};

export default PreviewPanel;