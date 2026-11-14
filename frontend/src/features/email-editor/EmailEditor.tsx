import React, { useState, useEffect } from 'react';
import { EmailDocument, EmailSection } from './types';
import BlockLibrary from './BlockLibrary';
import EmailCanvas from './EmailCanvas';
import PropertiesPanel from './PropertiesPanel';
import PreviewPanel from './PreviewPanel';
import AIChatPanel from './AIChatPanel';

interface EmailEditorProps {
  emailId?: string;
  projectId: string;
  onSave: (email: EmailDocument) => void;
}

const EmailEditor: React.FC<EmailEditorProps> = ({ emailId, projectId, onSave }) => {
  const [emailDocument, setEmailDocument] = useState<EmailDocument>({
    schema_version: 1,
    metadata: {
      name: 'New Email',
      subject: 'Email Subject',
      preheader: 'Email preheader text'
    },
    settings: {
      width: 600,
      background_color: '#F5F5F5',
      content_background: '#FFFFFF'
    },
    sections: []
  });

  const [selectedSectionId, setSelectedSectionId] = useState<string | null>(null);
  const [previewMode, setPreviewMode] = useState<'desktop' | 'mobile'>('desktop');
  const [isPreviewVisible, setIsPreviewVisible] = useState(false);

  // Find the selected section
  const selectedSection = emailDocument.sections.find(
    section => section.id === selectedSectionId
  );

  // Update sections in the email document
  const setEmailDocumentSections = (newSections: EmailSection[]) => {
    setEmailDocument({
      ...emailDocument,
      sections: newSections
    });
  };

  // Add a new section to the email
  const addSection = (type: string) => {
    const newSection: EmailSection = {
      id: `section-${Date.now()}`,
      type,
      props: getDefaultPropsForType(type)
    };

    setEmailDocument({
      ...emailDocument,
      sections: [...emailDocument.sections, newSection]
    });

    // Select the new section
    setSelectedSectionId(newSection.id);
  };

  // Get default props for a section type
  const getDefaultPropsForType = (type: string): any => {
    switch (type) {
      case 'header':
        return { text: 'Header Text' };
      case 'hero':
        return { 
          title: 'Hero Title', 
          subtitle: 'Hero subtitle text',
          alignment: 'center'
        };
      case 'heading':
        return { 
          text: 'Heading Text', 
          level: 2,
          alignment: 'left'
        };
      case 'paragraph':
        return { 
          content: 'Paragraph text goes here...', 
          alignment: 'left'
        };
      case 'image':
        return { 
          src: '', 
          alt: 'Image description',
          width: '100%',
          alignment: 'center'
        };
      case 'button':
        return { 
          label: 'Click Me', 
          url: '#',
          background_color: '#007bff',
          text_color: '#ffffff',
          border_radius: '4px',
          alignment: 'center'
        };
      case 'divider':
        return { 
          border_width: '1px',
          border_style: 'solid',
          border_color: '#cccccc'
        };
      case 'spacer':
        return { height: '20px' };
      case 'columns':
        return { 
          columns: [
            { id: 'col1', content: [] },
            { id: 'col2', content: [] }
          ]
        };
      case 'social':
        return { 
          links: [
            { platform: 'facebook', url: '#' },
            { platform: 'twitter', url: '#' }
          ]
        };
      case 'footer':
        return { text: 'Footer text' };
      case 'html':
        return { html: '<p>Custom HTML content</p>' };
      default:
        return {};
    }
  };

  // Update a section's properties
  const updateSectionProps = (sectionId: string, newProps: any) => {
    setEmailDocument({
      ...emailDocument,
      sections: emailDocument.sections.map(section =>
        section.id === sectionId ? { ...section, props: { ...section.props, ...newProps } } : section
      )
    });
  };

  // Move a section up or down
  const moveSection = (sectionId: string, direction: 'up' | 'down') => {
    const sections = [...emailDocument.sections];
    const index = sections.findIndex(section => section.id === sectionId);
    
    if (index === -1) return;
    
    if (direction === 'up' && index > 0) {
      [sections[index - 1], sections[index]] = [sections[index], sections[index - 1]];
    } else if (direction === 'down' && index < sections.length - 1) {
      [sections[index], sections[index + 1]] = [sections[index + 1], sections[index]];
    }
    
    setEmailDocument({
      ...emailDocument,
      sections
    });
  };

  // Delete a section
  const deleteSection = (sectionId: string) => {
    setEmailDocument({
      ...emailDocument,
      sections: emailDocument.sections.filter(section => section.id !== sectionId)
    });
    
    if (selectedSectionId === sectionId) {
      setSelectedSectionId(null);
    }
  };

  // Duplicate a section
  const duplicateSection = (sectionId: string) => {
    const section = emailDocument.sections.find(s => s.id === sectionId);
    if (!section) return;
    
    const duplicatedSection: EmailSection = {
      ...section,
      id: `section-${Date.now()}`,
      props: { ...section.props }
    };
    
    const index = emailDocument.sections.findIndex(s => s.id === sectionId);
    const newSections = [...emailDocument.sections];
    newSections.splice(index + 1, 0, duplicatedSection);
    
    setEmailDocument({
      ...emailDocument,
      sections: newSections
    });
  };

  // Save the email
  const handleSave = () => {
    onSave(emailDocument);
  };

  // State for AI chat panel
  const [isAIChatVisible, setIsAIChatVisible] = useState(false);
  
  // Toggle preview visibility
  const togglePreview = () => {
    setIsPreviewVisible(!isPreviewVisible);
  };

  // Toggle AI chat visibility
  const toggleAIChat = () => {
    setIsAIChatVisible(!isAIChatVisible);
  };

  // Handle applying AI operations to the email document
  const handleApplyOperations = (operations: any[], explanation: string) => {
    console.log('Applying operations:', operations);
    
    if (!operations || operations.length === 0) return;
    
    // Apply operations locally
    try {
      // In a real implementation, this would call the backend API
      // For now, apply operations locally
      let updatedDocument = { ...emailDocument };
      
      operations.forEach((op) => {
        switch (op.operation_type) {
          case "add_section":
            const newSection = {
              id: `section-${Date.now()}`,
              type: op.data.type,
              props: op.data.props || {}
            };
            updatedDocument.sections = [...updatedDocument.sections, newSection];
            break;
          
          case "update_section":
            updatedDocument.sections = updatedDocument.sections.map((section) => {
              if (section.id === op.section_id) {
                return {
                  ...section,
                  props: { ...section.props, ...op.data.props }
                };
              }
              return section;
            });
            break;
          
          case "remove_section":
            updatedDocument.sections = updatedDocument.sections.filter(
              (section) => section.id !== op.section_id
            );
            break;
          
          case "update_metadata":
            updatedDocument.metadata = {
              ...updatedDocument.metadata,
              ...op.data
            };
            break;
          
          case "update_global_style":
            updatedDocument.settings = {
              ...updatedDocument.settings,
              ...op.data
            };
            break;
        }
      });
      
      // Update the email document
      setEmailDocument(updatedDocument);
      console.log('Operations applied successfully:', explanation);
    } catch (error) {
      console.error('Failed to apply operations:', error);
    }
      const operation = operations[0];
      if (operation.operation_type === 'add_section') {
        addSection(operation.data.type);
      }
    }
    
    // Hide the AI chat panel after applying operations
    setIsAIChatVisible(false);
  };

  return (
    <div className="email-editor">
      <div className="editor-header">
        <h1>Email Editor</h1>
        <div className="editor-actions">
          <button onClick={handleSave}>Save</button>
          <button onClick={toggleAIChat}>
            {isAIChatVisible ? 'Hide AI Assistant' : 'Show AI Assistant'}
          </button>
          <button onClick={togglePreview}>
            {isPreviewVisible ? 'Hide Preview' : 'Show Preview'}
          </button>
        </div>
      </div>
      
      <div className="editor-layout">
        {/* Left Panel - Block Library */}
        <div className="panel panel-left">
          <BlockLibrary onAddSection={addSection} />
        </div>
        
        {/* Center Panel - Email Canvas */}
        <div className="panel panel-center">
          <EmailCanvas
            sections={emailDocument.sections}
            selectedSectionId={selectedSectionId}
            onSelectSection={setSelectedSectionId}
            onMoveSection={moveSection}
            onDeleteSection={deleteSection}
            onDuplicateSection={duplicateSection}
            onReorderSections={setEmailDocumentSections}
          />
        </div>
        
        {/* Right Panel - Properties and AI Chat */}
        <div className="panel panel-right">
          {selectedSection ? (
            <PropertiesPanel
              section={selectedSection}
              onUpdateProps={updateSectionProps}
            />
          ) : (
            <div className="global-settings">
              <h2>Email Settings</h2>
              <div className="property-group">
                <label>Name</label>
                <input
                  type="text"
                  value={emailDocument.metadata.name}
                  onChange={(e) => setEmailDocument({
                    ...emailDocument,
                    metadata: { ...emailDocument.metadata, name: e.target.value }
                  })}
                />
              </div>
              <div className="property-group">
                <label>Subject</label>
                <input
                  type="text"
                  value={emailDocument.metadata.subject}
                  onChange={(e) => setEmailDocument({
                    ...emailDocument,
                    metadata: { ...emailDocument.metadata, subject: e.target.value }
                  })}
                />
              </div>
              <div className="property-group">
                <label>Preheader</label>
                <textarea
                  value={emailDocument.metadata.preheader || ''}
                  onChange={(e) => setEmailDocument({
                    ...emailDocument,
                    metadata: { ...emailDocument.metadata, preheader: e.target.value }
                  })}
                />
              </div>
              <div className="property-group">
                <label>Width</label>
                <input
                  type="number"
                  value={emailDocument.settings.width}
                  onChange={(e) => setEmailDocument({
                    ...emailDocument,
                    settings: { ...emailDocument.settings, width: parseInt(e.target.value) }
                  })}
                />
              </div>
              <div className="property-group">
                <label>Background Color</label>
                <input
                  type="color"
                  value={emailDocument.settings.background_color}
                  onChange={(e) => setEmailDocument({
                    ...emailDocument,
                    settings: { ...emailDocument.settings, background_color: e.target.value }
                  })}
                />
              </div>
              <div className="property-group">
                <label>Content Background</label>
                <input
                  type="color"
                  value={emailDocument.settings.content_background}
                  onChange={(e) => setEmailDocument({
                    ...emailDocument,
                    settings: { ...emailDocument.settings, content_background: e.target.value }
                  })}
                />
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Preview Panel */}
      {isPreviewVisible && (
        <div className="preview-overlay">
          <div className="preview-container">
            <div className="preview-header">
              <h2>Email Preview</h2>
              <div className="preview-controls">
                <button 
                  className={previewMode === 'desktop' ? 'active' : ''}
                  onClick={() => setPreviewMode('desktop')}
                >
                  Desktop
                </button>
                <button 
                  className={previewMode === 'mobile' ? 'active' : ''}
                  onClick={() => setPreviewMode('mobile')}
                >
                  Mobile
                </button>
                <button onClick={togglePreview}>Close</button>
              </div>
            </div>
            <PreviewPanel 
              document={emailDocument} 
              mode={previewMode} 
            />
          </div>
        </div>
      )}
      
      {/* AI Chat Panel */}
      {isAIChatVisible && (
        <div className="ai-chat-overlay">
          <div className="ai-chat-container">
            <div className="ai-chat-header">
              <h2>PewPew AI Assistant</h2>
              <button onClick={toggleAIChat}>Close</button>
            </div>
            <AIChatPanel
              emailDocument={emailDocument}
              projectId={projectId}
              organizationId="org-placeholder" // In a real app, this would come from context
              emailId={emailId}
              onApplyOperations={handleApplyOperations}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default EmailEditor;