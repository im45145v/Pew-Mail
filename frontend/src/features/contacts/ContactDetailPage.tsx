import React, { useState, useEffect } from 'react';
import { Contact } from './types';
import { ContactService } from './services';

interface ContactDetailPageProps {
  contactId: string;
  onBack: () => void;
  onContactUpdated: () => void;
}

const ContactDetailPage: React.FC<ContactDetailPageProps> = ({ contactId, onBack, onContactUpdated }) => {
  const [contact, setContact] = useState<Contact | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState<Partial<Contact>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadContact();
  }, [contactId]);

  const loadContact = async () => {
    setLoading(true);
    try {
      const service = new ContactService();
      const contactData = await service.getContact(contactId);
      setContact(contactData);
      setFormData(contactData);
    } catch (err) {
      setError('Failed to load contact');
      console.error('Error loading contact:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSave = async () => {
    try {
      const service = new ContactService();
      await service.updateContact(contactId, formData);
      setEditing(false);
      onContactUpdated();
      loadContact(); // Reload to get updated data
    } catch (err) {
      setError('Failed to update contact');
      console.error('Error updating contact:', err);
    }
  };

  const handleArchive = async () => {
    try {
      const service = new ContactService();
      await service.archiveContact(contactId);
      onContactUpdated();
      onBack(); // Return to contacts list
    } catch (err) {
      setError('Failed to archive contact');
      console.error('Error archiving contact:', err);
    }
  };

  if (loading) {
    return <div className="loading">Loading contact...</div>;
  }

  if (error) {
    return (
      <div className="error-message">
        {error}
        <button onClick={onBack}>Back to Contacts</button>
      </div>
    );
  }

  if (!contact) {
    return (
      <div className="not-found">
        Contact not found.
        <button onClick={onBack}>Back to Contacts</button>
      </div>
    );
  }

  return (
    <div className="contact-detail-page">
      <div className="page-header">
        <button onClick={onBack} className="btn btn-secondary">← Back to Contacts</button>
        <h1>{editing ? 'Edit Contact' : 'Contact Details'}</h1>
        {!editing && (
          <div className="actions">
            <button onClick={() => setEditing(true)} className="btn btn-primary">Edit</button>
            <button onClick={handleArchive} className="btn btn-warning">Archive</button>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="contact-details">
        {editing ? (
          <form onSubmit={(e) => { e.preventDefault(); handleSave(); }}>
            <div className="form-group">
              <label htmlFor="first_name">First Name</label>
              <input
                type="text"
                id="first_name"
                name="first_name"
                value={formData.first_name || ''}
                onChange={handleInputChange}
              />
            </div>

            <div className="form-group">
              <label htmlFor="last_name">Last Name</label>
              <input
                type="text"
                id="last_name"
                name="last_name"
                value={formData.last_name || ''}
                onChange={handleInputChange}
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email || ''}
                onChange={handleInputChange}
              />
            </div>

            <div className="form-group">
              <label htmlFor="organization">Organization</label>
              <input
                type="text"
                id="organization"
                name="organization"
                value={formData.organization || ''}
                onChange={handleInputChange}
              />
            </div>

            <div className="form-group">
              <label htmlFor="job_title">Job Title</label>
              <input
                type="text"
                id="job_title"
                name="job_title"
                value={formData.job_title || ''}
                onChange={handleInputChange}
              />
            </div>

            <div className="form-group">
              <label htmlFor="phone_number">Phone Number</label>
              <input
                type="tel"
                id="phone_number"
                name="phone_number"
                value={formData.phone_number || ''}
                onChange={handleInputChange}
              />
            </div>

            <div className="form-group">
              <label htmlFor="notes">Notes</label>
              <textarea
                id="notes"
                name="notes"
                value={formData.notes || ''}
                onChange={handleInputChange}
                rows={4}
              />
            </div>

            <div className="form-actions">
              <button type="button" onClick={() => setEditing(false)} className="btn btn-secondary">
                Cancel
              </button>
              <button type="submit" className="btn btn-primary">
                Save Changes
              </button>
            </div>
          </form>
        ) : (
          <div className="contact-info">
            <div className="info-section">
              <h2>Personal Information</h2>
              <div className="info-row">
                <span className="label">Name:</span>
                <span className="value">{contact.first_name} {contact.last_name}</span>
              </div>
              <div className="info-row">
                <span className="label">Email:</span>
                <span className="value">{contact.email}</span>
              </div>
              <div className="info-row">
                <span className="label">Organization:</span>
                <span className="value">{contact.organization || 'Not specified'}</span>
              </div>
              <div className="info-row">
                <span className="label">Job Title:</span>
                <span className="value">{contact.job_title || 'Not specified'}</span>
              </div>
              <div className="info-row">
                <span className="label">Phone:</span>
                <span className="value">{contact.phone_number || 'Not specified'}</span>
              </div>
            </div>

            <div className="info-section">
              <h2>Contact Details</h2>
              <div className="info-row">
                <span className="label">Status:</span>
                <span className="value">
                  {contact.is_archived ? (
                    <span className="status archived">Archived</span>
                  ) : contact.is_suppressed ? (
                    <span className="status suppressed">Suppressed</span>
                  ) : (
                    <span className="status active">Active</span>
                  )}
                </span>
              </div>
              <div className="info-row">
                <span className="label">Consent Status:</span>
                <span className="value">{contact.consent_status || 'Not specified'}</span>
              </div>
              {contact.consent_timestamp && (
                <div className="info-row">
                  <span className="label">Consent Given:</span>
                  <span className="value">{new Date(contact.consent_timestamp).toLocaleDateString()}</span>
                </div>
              )}
              <div className="info-row">
                <span className="label">Source:</span>
                <span className="value">{contact.source || 'Not specified'}</span>
              </div>
            </div>

            <div className="info-section">
              <h2>Tags</h2>
              <div className="tags">
                {contact.tags && contact.tags.length > 0 ? (
                  contact.tags.map(tag => (
                    <span key={tag} className="tag">{tag}</span>
                  ))
                ) : (
                  <span className="empty">No tags</span>
                )}
              </div>
            </div>

            <div className="info-section">
              <h2>Notes</h2>
              <div className="notes">
                {contact.notes ? (
                  <p>{contact.notes}</p>
                ) : (
                  <span className="empty">No notes</span>
                )}
              </div>
            </div>

            <div className="info-section">
              <h2>Custom Fields</h2>
              {contact.custom_fields && Object.keys(contact.custom_fields).length > 0 ? (
                <div className="custom-fields">
                  {Object.entries(contact.custom_fields).map(([key, value]) => (
                    <div key={key} className="info-row">
                      <span className="label">{key}:</span>
                      <span className="value">{String(value)}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <span className="empty">No custom fields</span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ContactDetailPage;