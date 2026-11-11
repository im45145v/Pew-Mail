import React from 'react';
import { EmailSection } from './types';

interface PropertiesPanelProps {
  section: EmailSection;
  onUpdateProps: (sectionId: string, newProps: any) => void;
}

const PropertiesPanel: React.FC<PropertiesPanelProps> = ({ section, onUpdateProps }) => {
  const { id, type, props } = section;

  const updateProps = (newProps: any) => {
    onUpdateProps(id, newProps);
  };

  const renderProperties = () => {
    switch (type) {
      case 'header':
        return (
          <div className="property-group">
            <label>Text</label>
            <input
              type="text"
              value={props.text || ''}
              onChange={(e) => updateProps({ text: e.target.value })}
            />
          </div>
        );
      
      case 'hero':
        return (
          <>
            <div className="property-group">
              <label>Title</label>
              <input
                type="text"
                value={props.title || ''}
                onChange={(e) => updateProps({ title: e.target.value })}
              />
            </div>
            <div className="property-group">
              <label>Subtitle</label>
              <textarea
                value={props.subtitle || ''}
                onChange={(e) => updateProps({ subtitle: e.target.value })}
              />
            </div>
            <div className="property-group">
              <label>Alignment</label>
              <select
                value={props.alignment || 'center'}
                onChange={(e) => updateProps({ alignment: e.target.value })}
              >
                <option value="left">Left</option>
                <option value="center">Center</option>
                <option value="right">Right</option>
              </select>
            </div>
          </>
        );
      
      case 'heading':
        return (
          <>
            <div className="property-group">
              <label>Text</label>
              <input
                type="text"
                value={props.text || ''}
                onChange={(e) => updateProps({ text: e.target.value })}
              />
            </div>
            <div className="property-group">
              <label>Level</label>
              <select
                value={props.level || 2}
                onChange={(e) => updateProps({ level: parseInt(e.target.value) })}
              >
                <option value={1}>H1</option>
                <option value={2}>H2</option>
                <option value={3}>H3</option>
                <option value={4}>H4</option>
                <option value={5}>H5</option>
                <option value={6}>H6</option>
              </select>
            </div>
            <div className="property-group">
              <label>Alignment</label>
              <select
                value={props.alignment || 'left'}
                onChange={(e) => updateProps({ alignment: e.target.value })}
              >
                <option value="left">Left</option>
                <option value="center">Center</option>
                <option value="right">Right</option>
              </select>
            </div>
          </>
        );
      
      case 'paragraph':
        return (
          <>
            <div className="property-group">
              <label>Content</label>
              <textarea
                value={props.content || ''}
                onChange={(e) => updateProps({ content: e.target.value })}
                rows={4}
              />
            </div>
            <div className="property-group">
              <label>Alignment</label>
              <select
                value={props.alignment || 'left'}
                onChange={(e) => updateProps({ alignment: e.target.value })}
              >
                <option value="left">Left</option>
                <option value="center">Center</option>
                <option value="right">Right</option>
              </select>
            </div>
          </>
        );
      
      case 'image':
        return (
          <>
            <div className="property-group">
              <label>Image URL</label>
              <input
                type="text"
                value={props.src || ''}
                onChange={(e) => updateProps({ src: e.target.value })}
              />
            </div>
            <div className="property-group">
              <label>Alt Text</label>
              <input
                type="text"
                value={props.alt || ''}
                onChange={(e) => updateProps({ alt: e.target.value })}
              />
            </div>
            <div className="property-group">
              <label>Width</label>
              <input
                type="text"
                value={props.width || '100%'}
                onChange={(e) => updateProps({ width: e.target.value })}
              />
            </div>
            <div className="property-group">
              <label>Alignment</label>
              <select
                value={props.alignment || 'center'}
                onChange={(e) => updateProps({ alignment: e.target.value })}
              >
                <option value="left">Left</option>
                <option value="center">Center</option>
                <option value="right">Right</option>
              </select>
            </div>
          </>
        );
      
      case 'button':
        return (
          <>
            <div className="property-group">
              <label>Label</label>
              <input
                type="text"
                value={props.label || ''}
                onChange={(e) => updateProps({ label: e.target.value })}
              />
            </div>
            <div className="property-group">
              <label>URL</label>
              <input
                type="text"
                value={props.url || ''}
                onChange={(e) => updateProps({ url: e.target.value })}
              />
            </div>
            <div className="property-group">
              <label>Background Color</label>
              <input
                type="color"
                value={props.background_color || '#007bff'}
                onChange={(e) => updateProps({ background_color: e.target.value })}
              />
            </div>
            <div className="property-group">
              <label>Text Color</label>
              <input
                type="color"
                value={props.text_color || '#ffffff'}
                onChange={(e) => updateProps({ text_color: e.target.value })}
              />
            </div>
            <div className="property-group">
              <label>Border Radius</label>
              <input
                type="text"
                value={props.border_radius || '4px'}
                onChange={(e) => updateProps({ border_radius: e.target.value })}
              />
            </div>
            <div className="property-group">
              <label>Alignment</label>
              <select
                value={props.alignment || 'center'}
                onChange={(e) => updateProps({ alignment: e.target.value })}
              >
                <option value="left">Left</option>
                <option value="center">Center</option>
                <option value="right">Right</option>
              </select>
            </div>
          </>
        );
      
      case 'divider':
        return (
          <>
            <div className="property-group">
              <label>Border Width</label>
              <input
                type="text"
                value={props.border_width || '1px'}
                onChange={(e) => updateProps({ border_width: e.target.value })}
              />
            </div>
            <div className="property-group">
              <label>Border Style</label>
              <select
                value={props.border_style || 'solid'}
                onChange={(e) => updateProps({ border_style: e.target.value })}
              >
                <option value="solid">Solid</option>
                <option value="dashed">Dashed</option>
                <option value="dotted">Dotted</option>
              </select>
            </div>
            <div className="property-group">
              <label>Border Color</label>
              <input
                type="color"
                value={props.border_color || '#cccccc'}
                onChange={(e) => updateProps({ border_color: e.target.value })}
              />
            </div>
          </>
        );
      
      case 'spacer':
        return (
          <div className="property-group">
            <label>Height</label>
            <input
              type="text"
              value={props.height || '20px'}
              onChange={(e) => updateProps({ height: e.target.value })}
            />
          </div>
        );
      
      case 'columns':
        return (
          <div className="property-group">
            <label>Columns</label>
            <p>Columns component - edit in advanced mode</p>
          </div>
        );
      
      case 'social':
        return (
          <div className="property-group">
            <label>Social Links</label>
            <p>Social links component - edit in advanced mode</p>
          </div>
        );
      
      case 'footer':
        return (
          <div className="property-group">
            <label>Text</label>
            <textarea
              value={props.text || ''}
              onChange={(e) => updateProps({ text: e.target.value })}
              rows={3}
            />
          </div>
        );
      
      case 'html':
        return (
          <div className="property-group">
            <label>HTML Content</label>
            <textarea
              value={props.html || ''}
              onChange={(e) => updateProps({ html: e.target.value })}
              rows={6}
            />
          </div>
        );
      
      default:
        return (
          <div className="property-group">
            <p>Properties for {type} component</p>
          </div>
        );
    }
  };

  return (
    <div className="properties-panel">
      <h2>{type.charAt(0).toUpperCase() + type.slice(1)} Properties</h2>
      {renderProperties()}
    </div>
  );
};

export default PropertiesPanel;