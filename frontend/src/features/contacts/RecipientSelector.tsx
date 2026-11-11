import React, { useState, useEffect } from 'react';
import { Contact, ContactGroup, RecipientSelectionRequest, RecipientSummaryResponse } from './types';
import { ContactService } from './services';

interface RecipientSelectorProps {
  organizationId: string;
  selectedRecipients: string[]; // Contact IDs
  selectedGroups: string[]; // Group IDs
  onRecipientsChange: (contactIds: string[]) => void;
  onGroupsChange: (groupIds: string[]) => void;
  onSummaryChange: (summary: RecipientSummaryResponse | null) => void;
}

const RecipientSelector: React.FC<RecipientSelectorProps> = ({
  organizationId,
  selectedRecipients,
  selectedGroups,
  onRecipientsChange,
  onGroupsChange,
  onSummaryChange
}) => {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [groups, setGroups] = useState<ContactGroup[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredContacts, setFilteredContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<RecipientSummaryResponse | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);

  useEffect(() => {
    loadContactsAndGroups();
  }, [organizationId]);

  useEffect(() => {
    filterContacts();
  }, [searchQuery, contacts]);

  useEffect(() => {
    calculateSummary();
  }, [selectedRecipients, selectedGroups]);

  const loadContactsAndGroups = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const service = new ContactService();
      const [contactsData, groupsData] = await Promise.all([
        service.searchContacts(organizationId, {}),
        service.listGroups(organizationId)
      ]);
      
      setContacts(contactsData);
      setGroups(groupsData);
      setFilteredContacts(contactsData);
    } catch (err) {
      setError('Failed to load contacts and groups');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterContacts = () => {
    if (!searchQuery.trim()) {
      setFilteredContacts(contacts);
      return;
    }
    
    const query = searchQuery.toLowerCase();
    const filtered = contacts.filter(contact =>
      contact.first_name.toLowerCase().includes(query) ||
      contact.last_name.toLowerCase().includes(query) ||
      contact.email.toLowerCase().includes(query) ||
      (contact.organization && contact.organization.toLowerCase().includes(query))
    );
    
    setFilteredContacts(filtered);
  };

  const calculateSummary = async () => {
    try {
      const service = new ContactService();
      const request: RecipientSelectionRequest = {
        contact_ids: selectedRecipients,
        group_ids: selectedGroups
      };
      
      const summaryData = await service.getRecipientSummary(organizationId, request);
      setSummary(summaryData);
      onSummaryChange(summaryData);
    } catch (err) {
      console.error('Error calculating recipient summary:', err);
      setSummary(null);
      onSummaryChange(null);
    }
  };

  const handleContactToggle = (contactId: string) => {
    if (selectedRecipients.includes(contactId)) {
      onRecipientsChange(selectedRecipients.filter(id => id !== contactId));
    } else {
      onRecipientsChange([...selectedRecipients, contactId]);
    }
  };

  const handleGroupToggle = (groupId: string) => {
    if (selectedGroups.includes(groupId)) {
      onGroupsChange(selectedGroups.filter(id => id !== groupId));
    } else {
      onGroupsChange([...selectedGroups, groupId]);
    }
  };

  const isSelectedContact = (contactId: string) => {
    return selectedRecipients.includes(contactId);
  };

  const isSelectedGroup = (groupId: string) => {
    return selectedGroups.includes(groupId);
  };

  return (
    <div className="recipient-selector">
      <div className="selector-header">
        <h3>Select Recipients</h3>
        <div className="recipient-summary">
          {summary ? (
            <span>
              {summary.total_recipients} recipient{summary.total_recipients !== 1 ? 's' : ''} •{' '}
              {summary.unique_domains} domain{summary.unique_domains !== 1 ? 's' : ''}
            </span>
          ) : (
            <span>No recipients selected</span>
          )}
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="selection-controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search contacts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onFocus={() => setShowDropdown(true)}
            onBlur={() => setTimeout(() => setShowDropdown(false), 200)}
          />
        </div>

        <div className="selection-buttons">
          <button 
            className="btn btn-secondary"
            onClick={() => {
              onRecipientsChange([]);
              onGroupsChange([]);
            }}
          >
            Clear All
          </button>
        </div>
      </div>

      {showDropdown && (
        <div className="dropdown-container">
          <div className="dropdown-content">
            <div className="dropdown-section">
              <h4>Contacts</h4>
              {loading ? (
                <div className="loading">Loading contacts...</div>
              ) : filteredContacts.length > 0 ? (
                <ul className="contact-list">
                  {filteredContacts.slice(0, 10).map(contact => (
                    <li 
                      key={contact.id}
                      className={`contact-item ${isSelectedContact(contact.id) ? 'selected' : ''}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleContactToggle(contact.id);
                      }}
                    >
                      <div className="contact-checkbox">
                        <input
                          type="checkbox"
                          checked={isSelectedContact(contact.id)}
                          onChange={() => {}} // Handled by parent div onClick
                        />
                      </div>
                      <div className="contact-info">
                        <div className="contact-name">
                          {contact.first_name} {contact.last_name}
                        </div>
                        <div className="contact-email">
                          {contact.email}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="no-results">
                  No contacts found
                </div>
              )}
            </div>

            <div className="dropdown-section">
              <h4>Groups</h4>
              {groups.length > 0 ? (
                <ul className="group-list">
                  {groups.map(group => (
                    <li 
                      key={group.id}
                      className={`group-item ${isSelectedGroup(group.id) ? 'selected' : ''}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleGroupToggle(group.id);
                      }}
                    >
                      <div className="group-checkbox">
                        <input
                          type="checkbox"
                          checked={isSelectedGroup(group.id)}
                          onChange={() => {}} // Handled by parent div onClick
                        />
                      </div>
                      <div className="group-info">
                        <div className="group-name">
                          {group.name}
                        </div>
                        <div className="group-count">
                          {group.member_count} members
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="no-results">
                  No groups available
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {(selectedRecipients.length > 0 || selectedGroups.length > 0) && (
        <div className="selected-recipients">
          <h4>Selected Recipients</h4>
          
          {selectedGroups.length > 0 && (
            <div className="selected-groups">
              {selectedGroups.map(groupId => {
                const group = groups.find(g => g.id === groupId);
                return group ? (
                  <div key={groupId} className="selected-tag group-tag">
                    <span className="tag-label">
                      {group.name} ({group.member_count})
                    </span>
                    <button 
                      className="remove-btn"
                      onClick={() => handleGroupToggle(groupId)}
                    >
                      ×
                    </button>
                  </div>
                ) : null;
              })}
            </div>
          )}
          
          {selectedRecipients.length > 0 && (
            <div className="selected-contacts">
              {selectedRecipients.map(contactId => {
                const contact = contacts.find(c => c.id === contactId);
                return contact ? (
                  <div key={contactId} className="selected-tag contact-tag">
                    <span className="tag-label">
                      {contact.first_name} {contact.last_name}
                    </span>
                    <button 
                      className="remove-btn"
                      onClick={() => handleContactToggle(contactId)}
                    >
                      ×
                    </button>
                  </div>
                ) : null;
              })}
            </div>
          )}
        </div>
      )}

      {summary && (
        <div className="validation-summary">
          <h4>Validation Summary</h4>
          <div className="summary-details">
            <div className="summary-item">
              <span className="label">Total Recipients:</span>
              <span className="value">{summary.total_recipients}</span>
            </div>
            <div className="summary-item">
              <span className="label">Unique Domains:</span>
              <span className="value">{summary.unique_domains}</span>
            </div>
            <div className="summary-item">
              <span className="label">Suppressed Emails:</span>
              <span className="value">{summary.suppressed_count}</span>
            </div>
            <div className="summary-item">
              <span className="label">Invalid Emails:</span>
              <span className="value">{summary.invalid_count}</span>
            </div>
          </div>
          
          {summary.warnings.length > 0 && (
            <div className="warnings">
              {summary.warnings.map((warning, index) => (
                <div key={index} className="warning-item">
                  {warning}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RecipientSelector;