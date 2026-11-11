import React, { useState, useEffect } from 'react';
import { ContactGroup, Contact } from './types';
import { ContactService } from './services';

interface GroupsPageProps {
  organizationId: string;
}

const GroupsPage: React.FC<GroupsPageProps> = ({ organizationId }) => {
  const [groups, setGroups] = useState<ContactGroup[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<ContactGroup | null>(null);
  const [groupMembers, setGroupMembers] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupDescription, setNewGroupDescription] = useState('');

  useEffect(() => {
    loadGroups();
  }, [organizationId]);

  useEffect(() => {
    if (selectedGroup) {
      loadGroupMembers(selectedGroup.id);
    } else {
      setGroupMembers([]);
    }
  }, [selectedGroup]);

  const loadGroups = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const service = new ContactService();
      const results = await service.listGroups(organizationId);
      setGroups(results);
    } catch (err) {
      setError('Failed to load groups');
      console.error('Error loading groups:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadGroupMembers = async (groupId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const service = new ContactService();
      const members = await service.getGroupMembers(groupId);
      setGroupMembers(members);
    } catch (err) {
      setError('Failed to load group members');
      console.error('Error loading group members:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) {
      setError('Group name is required');
      return;
    }

    try {
      const service = new ContactService();
      const groupData = {
        name: newGroupName,
        description: newGroupDescription
      };
      
      await service.createGroup(organizationId, groupData);
      setShowCreateForm(false);
      setNewGroupName('');
      setNewGroupDescription('');
      loadGroups(); // Refresh the groups list
    } catch (err) {
      setError('Failed to create group');
      console.error('Error creating group:', err);
    }
  };

  const handleDeleteGroup = async (groupId: string) => {
    if (!window.confirm('Are you sure you want to delete this group?')) {
      return;
    }

    try {
      const service = new ContactService();
      await service.deleteGroup(groupId);
      if (selectedGroup?.id === groupId) {
        setSelectedGroup(null);
      }
      loadGroups(); // Refresh the groups list
    } catch (err) {
      setError('Failed to delete group');
      console.error('Error deleting group:', err);
    }
  };

  const handleAddToGroup = async (contactId: string) => {
    if (!selectedGroup) return;

    try {
      const service = new ContactService();
      await service.addContactToGroup(selectedGroup.id, contactId);
      loadGroupMembers(selectedGroup.id); // Refresh members list
    } catch (err) {
      setError('Failed to add contact to group');
      console.error('Error adding contact to group:', err);
    }
  };

  const handleRemoveFromGroup = async (contactId: string) => {
    if (!selectedGroup) return;

    try {
      const service = new ContactService();
      await service.removeContactFromGroup(selectedGroup.id, contactId);
      loadGroupMembers(selectedGroup.id); // Refresh members list
    } catch (err) {
      setError('Failed to remove contact from group');
      console.error('Error removing contact from group:', err);
    }
  };

  return (
    <div className="groups-page">
      <div className="groups-header">
        <h1>Contact Groups</h1>
        <button 
          className="btn btn-primary"
          onClick={() => setShowCreateForm(true)}
        >
          Create Group
        </button>
      </div>

      {showCreateForm && (
        <div className="create-group-form">
          <h2>Create New Group</h2>
          {error && !selectedGroup && (
            <div className="error-message">
              {error}
            </div>
          )}
          <div className="form-group">
            <label htmlFor="group-name">Group Name</label>
            <input
              type="text"
              id="group-name"
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
              placeholder="Enter group name"
            />
          </div>
          <div className="form-group">
            <label htmlFor="group-description">Description</label>
            <textarea
              id="group-description"
              value={newGroupDescription}
              onChange={(e) => setNewGroupDescription(e.target.value)}
              placeholder="Enter group description (optional)"
              rows={3}
            />
          </div>
          <div className="form-actions">
            <button 
              className="btn btn-secondary"
              onClick={() => {
                setShowCreateForm(false);
                setNewGroupName('');
                setNewGroupDescription('');
                setError(null);
              }}
            >
              Cancel
            </button>
            <button 
              className="btn btn-primary"
              onClick={handleCreateGroup}
            >
              Create Group
            </button>
          </div>
        </div>
      )}

      {error && !showCreateForm && (
        <div className="error-message">
          {error}
        </div>
      )}

      <div className="groups-content">
        <div className="groups-list">
          <h2>Groups</h2>
          {loading && !selectedGroup ? (
            <div className="loading">Loading groups...</div>
          ) : (
            <ul className="group-items">
              {groups.map((group) => (
                <li 
                  key={group.id}
                  className={`group-item ${selectedGroup?.id === group.id ? 'selected' : ''}`}
                  onClick={() => setSelectedGroup(group)}
                >
                  <div className="group-info">
                    <h3>{group.name}</h3>
                    <p>{group.description || 'No description'}</p>
                    <span className="member-count">{group.member_count} members</span>
                  </div>
                  <div className="group-actions">
                    <button 
                      className="btn btn-danger"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteGroup(group.id);
                      }}
                    >
                      Delete
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          )}
          
          {groups.length === 0 && !loading && (
            <div className="no-groups">
              No groups found. <button 
                className="btn btn-link"
                onClick={() => setShowCreateForm(true)}
              >
                Create your first group
              </button>
            </div>
          )}
        </div>

        {selectedGroup && (
          <div className="group-details">
            <div className="group-details-header">
              <h2>{selectedGroup.name}</h2>
              <button 
                className="btn btn-secondary"
                onClick={() => setSelectedGroup(null)}
              >
                Close
              </button>
            </div>
            
            {selectedGroup.description && (
              <p className="group-description">{selectedGroup.description}</p>
            )}
            
            <div className="group-members">
              <div className="members-header">
                <h3>Members ({groupMembers.length})</h3>
              </div>
              
              {loading ? (
                <div className="loading">Loading members...</div>
              ) : (
                <div className="members-list">
                  {groupMembers.map((contact) => (
                    <div key={contact.id} className="member-item">
                      <div className="member-info">
                        <span className="member-name">
                          {contact.first_name} {contact.last_name}
                        </span>
                        <span className="member-email">{contact.email}</span>
                      </div>
                      <div className="member-actions">
                        <button 
                          className="btn btn-warning"
                          onClick={() => handleRemoveFromGroup(contact.id)}
                        >
                          Remove
                        </button>
                      </div>
                    </div>
                  ))}
                  
                  {groupMembers.length === 0 && (
                    <div className="no-members">
                      This group has no members.
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GroupsPage;