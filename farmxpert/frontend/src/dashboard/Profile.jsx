import React, { useState } from 'react';
import { User, Mail, Phone, MapPin, Calendar, Edit, Save, X, Sprout, Award } from 'lucide-react';
import '../styles/Dashboard/Profile/profile.css';

const Profile = () => {
  const [isEditing, setIsEditing] = useState(false);
  const [profileData, setProfileData] = useState({
    name: 'John Farmer',
    email: 'john.farmer@example.com',
    phone: '+1 (555) 123-4567',
    location: 'Ahmedabad, Gujarat',
    joinDate: 'January 15, 2024',
    farmSize: '15 acres',
    experience: '5 years'
  });

  const [editData, setEditData] = useState(profileData);

  const handleEdit = () => {
    setEditData(profileData);
    setIsEditing(true);
  };

  const handleSave = () => {
    setProfileData(editData);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditData(profileData);
    setIsEditing(false);
  };

  const handleInputChange = (field, value) => {
    setEditData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div className="container-profile">
      <div className="wrapper-profile">
        {/* Profile Card */}
        <div className="card-profile">
          {/* Header Section */}
          <div className="header-profile">
            <div className="header-bg-profile"></div>
            <div className="header-content-profile">
              <div className="avatar-profile">
                <User size={48} strokeWidth={2} />
              </div>
              <div className="info-profile">
                <h1 className="name-profile">{profileData.name}</h1>
                <p className="role-profile">Professional Farmer</p>
              </div>
              <div className="actions-profile">
                {!isEditing ? (
                  <button onClick={handleEdit} className="btn-edit-profile">
                    <Edit size={18} />
                    <span>Edit Profile</span>
                  </button>
                ) : (
                  <div className="actions-group-profile">
                    <button onClick={handleSave} className="btn-save-profile">
                      <Save size={18} />
                      <span>Save</span>
                    </button>
                    <button onClick={handleCancel} className="btn-cancel-profile">
                      <X size={18} />
                      <span>Cancel</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Stats Section */}
          <div className="stats-profile">
            <div className="stat-item-profile">
              <div className="stat-icon-profile">
                <Sprout size={24} />
              </div>
              <div className="stat-content-profile">
                <p className="stat-value-profile">{profileData.farmSize}</p>
                <p className="stat-label-profile">Farm Size</p>
              </div>
            </div>
            <div className="stat-item-profile">
              <div className="stat-icon-profile">
                <Award size={24} />
              </div>
              <div className="stat-content-profile">
                <p className="stat-value-profile">{profileData.experience}</p>
                <p className="stat-label-profile">Experience</p>
              </div>
            </div>
            <div className="stat-item-profile">
              <div className="stat-icon-profile">
                <Calendar size={24} />
              </div>
              <div className="stat-content-profile">
                <p className="stat-value-profile">Member</p>
                <p className="stat-label-profile">Since 2024</p>
              </div>
            </div>
          </div>

          {/* Details Section */}
          <div className="details-profile">
            {/* Personal Information */}
            <div className="section-profile">
              <div className="section-header-profile">
                <h2 className="section-title-profile">Personal Information</h2>
                <div className="section-divider-profile"></div>
              </div>
              <div className="grid-profile">
                <div className="field-profile">
                  <div className="field-icon-profile">
                    <Mail size={20} />
                  </div>
                  <div className="field-content-profile">
                    <label className="field-label-profile">Email Address</label>
                    {isEditing ? (
                      <input
                        type="email"
                        value={editData.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        className="field-input-profile"
                        placeholder="Enter email address"
                      />
                    ) : (
                      <p className="field-value-profile">{profileData.email}</p>
                    )}
                  </div>
                </div>

                <div className="field-profile">
                  <div className="field-icon-profile">
                    <Phone size={20} />
                  </div>
                  <div className="field-content-profile">
                    <label className="field-label-profile">Phone Number</label>
                    {isEditing ? (
                      <input
                        type="tel"
                        value={editData.phone}
                        onChange={(e) => handleInputChange('phone', e.target.value)}
                        className="field-input-profile"
                        placeholder="Enter phone number"
                      />
                    ) : (
                      <p className="field-value-profile">{profileData.phone}</p>
                    )}
                  </div>
                </div>

                <div className="field-profile">
                  <div className="field-icon-profile">
                    <MapPin size={20} />
                  </div>
                  <div className="field-content-profile">
                    <label className="field-label-profile">Location</label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={editData.location}
                        onChange={(e) => handleInputChange('location', e.target.value)}
                        className="field-input-profile"
                        placeholder="Enter location"
                      />
                    ) : (
                      <p className="field-value-profile">{profileData.location}</p>
                    )}
                  </div>
                </div>

                <div className="field-profile">
                  <div className="field-icon-profile">
                    <Calendar size={20} />
                  </div>
                  <div className="field-content-profile">
                    <label className="field-label-profile">Member Since</label>
                    <p className="field-value-profile">{profileData.joinDate}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Farm Information */}
            <div className="section-profile">
              <div className="section-header-profile">
                <h2 className="section-title-profile">Farm Information</h2>
                <div className="section-divider-profile"></div>
              </div>
              <div className="grid-profile">
                <div className="field-profile">
                  <div className="field-icon-profile">
                    <Sprout size={20} />
                  </div>
                  <div className="field-content-profile">
                    <label className="field-label-profile">Farm Size</label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={editData.farmSize}
                        onChange={(e) => handleInputChange('farmSize', e.target.value)}
                        className="field-input-profile"
                        placeholder="Enter farm size"
                      />
                    ) : (
                      <p className="field-value-profile">{profileData.farmSize}</p>
                    )}
                  </div>
                </div>

                <div className="field-profile">
                  <div className="field-icon-profile">
                    <Award size={20} />
                  </div>
                  <div className="field-content-profile">
                    <label className="field-label-profile">Farming Experience</label>
                    {isEditing ? (
                      <input
                        type="text"
                        value={editData.experience}
                        onChange={(e) => handleInputChange('experience', e.target.value)}
                        className="field-input-profile"
                        placeholder="Enter experience"
                      />
                    ) : (
                      <p className="field-value-profile">{profileData.experience}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;