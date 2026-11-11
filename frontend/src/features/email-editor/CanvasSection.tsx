import React, { useState } from 'react';
import { EmailSection } from './types';

interface CanvasSectionProps {
  section: EmailSection;
  isSelected: boolean;
  isFirst: boolean;
  isLast: boolean;
  onSelect: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
}

const CanvasSection: React.FC<CanvasSectionProps> = ({
  section,
  isSelected,
  isFirst,
  isLast,
  onSelect,
  onMoveUp,
  onMoveDown,
  onDelete,
  onDuplicate
}) => {
  const [isDragOver, setIsDragOver] = useState(false);

  // Handle drag over event
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setIsDragOver(true);
  };

  // Handle drag leave event
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  // Handle drop event
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const renderSectionPreview = () => {
    const { type, props } = section;
    
    switch (type) {
      case 'header':
        return <div className="section-preview header">{props.text || 'Header Text'}</div>;
      
      case 'hero':
        return (
          <div className="section-preview hero">
            <h1>{props.title || 'Hero Title'}</h1>
            {props.subtitle && <p>{props.subtitle}</p>}
          </div>
        );
      
      case 'heading':
        const HeadingTag = `h${props.level || 2}` as keyof JSX.IntrinsicElements;
        return (
          <div className="section-preview heading">
            <HeadingTag>{props.text || 'Heading Text'}</HeadingTag>
          </div>
        );
      
      case 'paragraph':
        return (
          <div className="section-preview paragraph">
            {props.content || 'Paragraph text...'}
          </div>
        );
      
      case 'image':
        return (
          <div className="section-preview image">
            {props.src ? (
              <img src={props.src} alt={props.alt || 'Image'} />
            ) : (
              <div className="placeholder">[Image Placeholder]</div>
            )}
          </div>
        );
      
      case 'button':
        return (
          <div className="section-preview button">
            <button style={{
              backgroundColor: props.background_color || '#007bff',
              color: props.text_color || '#ffffff',
              borderRadius: props.border_radius || '4px'
            }}>
              {props.label || 'Button'}
            </button>
          </div>
        );
      
      case 'divider':
        return (
          <div className="section-preview divider">
            <hr style={{
              borderWidth: props.border_width || '1px',
              borderStyle: props.border_style || 'solid',
              borderColor: props.border_color || '#cccccc'
            }} />
          </div>
        );
      
      case 'spacer':
        return (
          <div className="section-preview spacer">
            <div style={{ height: props.height || '20px' }}></div>
          </div>
        );
      
      case 'columns':
        return (
          <div className="section-preview columns">
            <div className="columns-container">
              {(props.columns || []).map((column: any, index: number) => (
                <div key={index} className="column">
                  <span>Column {index + 1}</span>
                </div>
              ))}
            </div>
          </div>
        );
      
      case 'social':
        return (
          <div className="section-preview social">
            Social Links: {(props.links || []).length} platforms
          </div>
        );
      
      case 'footer':
        return (
          <div className="section-preview footer">
            {props.text || 'Footer text'}
          </div>
        );
      
      case 'html':
        return (
          <div className="section-preview html">
            <pre>{props.html || '<p>Custom HTML</p>'}</pre>
          </div>
        );
      
      default:
        return <div className="section-preview unknown">Unknown section type: {type}</div>;
    }
  };

  return (
    <div 
      className={`canvas-section ${isSelected ? 'selected' : ''} ${isDragOver ? 'drag-over' : ''}`}
      onClick={onSelect}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className="section-toolbar">
        <div className="section-type">{section.type}</div>
        <div className="section-actions">
          <button 
            onClick={(e) => { e.stopPropagation(); onMoveUp(); }}
            disabled={isFirst}
            title="Move up"
          >
            ↑
          </button>
          <button 
            onClick={(e) => { e.stopPropagation(); onMoveDown(); }}
            disabled={isLast}
            title="Move down"
          >
            ↓
          </button>
          <button 
            onClick={(e) => { e.stopPropagation(); onDuplicate(); }}
            title="Duplicate"
          >
            📋
          </button>
          <button 
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
            title="Delete"
          >
            🗑️
          </button>
        </div>
      </div>
      
      <div className="section-content">
        {renderSectionPreview()}
      </div>
    </div>
  );
};

export default CanvasSection;