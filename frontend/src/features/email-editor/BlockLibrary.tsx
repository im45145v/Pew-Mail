import React from 'react';
import { BlockType } from './types';

interface BlockLibraryProps {
  onAddSection: (type: string) => void;
}

const BlockLibrary: React.FC<BlockLibraryProps> = ({ onAddSection }) => {
  const blockCategories: { name: string; blocks: BlockType[] }[] = [
    {
      name: 'Layout',
      blocks: [
        {
          id: 'header',
          name: 'Header',
          icon: '📝',
          category: 'layout',
          description: 'Add a header section'
        },
        {
          id: 'hero',
          name: 'Hero',
          icon: '🌟',
          category: 'layout',
          description: 'Add a hero section with title and subtitle'
        },
        {
          id: 'columns',
          name: 'Columns',
          icon: '📊',
          category: 'layout',
          description: 'Add a multi-column layout'
        },
        {
          id: 'footer',
          name: 'Footer',
          icon: '📑',
          category: 'layout',
          description: 'Add a footer section'
        }
      ]
    },
    {
      name: 'Content',
      blocks: [
        {
          id: 'heading',
          name: 'Heading',
          icon: '🔤',
          category: 'content',
          description: 'Add a heading'
        },
        {
          id: 'paragraph',
          name: 'Paragraph',
          icon: '📄',
          category: 'content',
          description: 'Add a paragraph of text'
        },
        {
          id: 'image',
          name: 'Image',
          icon: '🖼️',
          category: 'content',
          description: 'Add an image'
        },
        {
          id: 'button',
          name: 'Button',
          icon: '🔘',
          category: 'content',
          description: 'Add a call-to-action button'
        }
      ]
    },
    {
      name: 'Utilities',
      blocks: [
        {
          id: 'divider',
          name: 'Divider',
          icon: '➖',
          category: 'utilities',
          description: 'Add a horizontal divider'
        },
        {
          id: 'spacer',
          name: 'Spacer',
          icon: '⏸️',
          category: 'utilities',
          description: 'Add vertical spacing'
        },
        {
          id: 'social',
          name: 'Social Links',
          icon: '🔗',
          category: 'utilities',
          description: 'Add social media links'
        },
        {
          id: 'html',
          name: 'HTML',
          icon: '</>',
          category: 'utilities',
          description: 'Add custom HTML'
        }
      ]
    }
  ];

  return (
    <div className="block-library">
      <h2>Blocks</h2>
      {blockCategories.map(category => (
        <div key={category.name} className="block-category">
          <h3>{category.name}</h3>
          <div className="blocks-grid">
            {category.blocks.map(block => (
              <div
                key={block.id}
                className="block-item"
                onClick={() => onAddSection(block.id)}
                title={block.description}
              >
                <div className="block-icon">{block.icon}</div>
                <div className="block-name">{block.name}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

export default BlockLibrary;