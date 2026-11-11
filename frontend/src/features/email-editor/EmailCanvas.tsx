import React, { useState } from 'react';
import { EmailSection } from './types';
import CanvasSection from './CanvasSection';

interface EmailCanvasProps {
  sections: EmailSection[];
  selectedSectionId: string | null;
  onSelectSection: (id: string) => void;
  onMoveSection: (id: string, direction: 'up' | 'down') => void;
  onDeleteSection: (id: string) => void;
  onDuplicateSection: (id: string) => void;
  onReorderSections: (newSections: EmailSection[]) => void;
}

const EmailCanvas: React.FC<EmailCanvasProps> = ({
  sections,
  selectedSectionId,
  onSelectSection,
  onMoveSection,
  onDeleteSection,
  onDuplicateSection,
  onReorderSections
}) => {
  const [draggedSectionId, setDraggedSectionId] = useState<string | null>(null);

  const handleDragStart = (e: React.DragEvent, sectionId: string) => {
    setDraggedSectionId(sectionId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e: React.DragEvent, targetSectionId: string) => {
    e.preventDefault();
    
    if (!draggedSectionId || draggedSectionId === targetSectionId) {
      return;
    }

    // Reorder sections
    const draggedIndex = sections.findIndex(section => section.id === draggedSectionId);
    const targetIndex = sections.findIndex(section => section.id === targetSectionId);
    
    if (draggedIndex === -1 || targetIndex === -1) {
      return;
    }

    const newSections = [...sections];
    const [draggedSection] = newSections.splice(draggedIndex, 1);
    newSections.splice(targetIndex, 0, draggedSection);
    
    onReorderSections(newSections);
    setDraggedSectionId(null);
  };

  const handleDragEnd = () => {
    setDraggedSectionId(null);
  };

  return (
    <div className="email-canvas">
      <div className="canvas-header">
        <h2>Email Content</h2>
        <p>Click on a section to edit its properties. Drag to reorder.</p>
      </div>
      
      {sections.length === 0 ? (
        <div className="empty-state">
          <p>No sections added yet</p>
          <p>Add blocks from the library to get started</p>
        </div>
      ) : (
        <div className="canvas-content">
          {sections.map((section, index) => (
            <div
              key={section.id}
              draggable
              onDragStart={(e) => handleDragStart(e, section.id)}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, section.id)}
              onDragEnd={handleDragEnd}
            >
              <CanvasSection
                section={section}
                isSelected={section.id === selectedSectionId}
                isFirst={index === 0}
                isLast={index === sections.length - 1}
                onSelect={() => onSelectSection(section.id)}
                onMoveUp={() => onMoveSection(section.id, 'up')}
                onMoveDown={() => onMoveSection(section.id, 'down')}
                onDelete={() => onDeleteSection(section.id)}
                onDuplicate={() => onDuplicateSection(section.id)}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EmailCanvas;