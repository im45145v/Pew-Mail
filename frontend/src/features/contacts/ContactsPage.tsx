import React, { useState, useEffect } from 'react';
import { Contact, SearchContactsRequest } from './types';
import { ContactService } from './services';

interface ContactsPageProps {
  organizationId: string;
}

const ContactsPage: React.FC<ContactsPageProps> = ({ organizationId }) => {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadContacts();
  }, [organizationId]);

  const loadContacts = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const service = new ContactService();
      const searchRequest: SearchContactsRequest = {
        query: searchQuery || undefined,
        include_archived: false
      };
      
      const results = await service.searchContacts(organizationId, searchRequest);
      setContacts(results);
    } catch (err) {
      setError('Failed to load contacts');
      console.error('Error loading contacts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadContacts();
  };

  const handleArchiveContact = async (contactId: string) => {
    try {
      const service = new ContactService();
      await service.archiveContact(contactId);
      // Refresh the contact list
      loadContacts();
    } catch (err) {
      setError('Failed to archive contact');
      console.error('Error archiving contact:', err);
    }
  };

  return (
    <div className="contacts-page">
      <div className="contacts-header">
        <h1>Contacts</h1>
        <button className="btn btn-primary">Add Contact</button>
      </div>

      <div className="contacts-search">
        <form onSubmit={handleSearch}>
          <input
            type="text"
            placeholder="Search contacts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button type="submit">Search</button>
        </form>
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {loading ? (
        <div className="loading">Loading contacts...</div>
      ) : (
        <div className="contacts-table">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Organization</th>
                <th>Job Title</th>
                <th>Tags</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {contacts.map((contact) => (
                <tr key={contact.id}>
                  <td>{contact.first_name} {contact.last_name}</td>
                  <td>{contact.email}</td>
                  <td>{contact.organization}</td>
                  <td>{contact.job_title}</td>
                  <td>
                    {contact.tags?.map((tag) => (
                      <span key={tag} className="tag">{tag}</span>
                    ))}
                  </td>
                  <td>
                    <button className="btn btn-secondary">Edit</button>
                    <button 
                      className="btn btn-warning"
                      onClick={() => handleArchiveContact(contact.id)}
                    >
                      Archive
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {contacts.length === 0 && (
            <div className="no-contacts">
              No contacts found. <button className="btn btn-link">Add your first contact</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ContactsPage;