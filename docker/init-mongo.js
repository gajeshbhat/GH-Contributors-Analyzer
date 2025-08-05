// MongoDB initialization script
// This script runs when the MongoDB container starts for the first time

// Switch to the github_contributors database
db = db.getSiblingDB('github_contributors');

// Create collections with proper indexes
db.createCollection('repositories');
db.createCollection('contributors');
db.createCollection('topics');

// Create indexes for better query performance
db.repositories.createIndex({ "name": 1, "owner": 1 }, { unique: true });
db.repositories.createIndex({ "topics": 1 });
db.repositories.createIndex({ "stargazers_count": -1 });
db.repositories.createIndex({ "created_at": -1 });
db.repositories.createIndex({ "updated_at": -1 });

db.contributors.createIndex({ "repository_id": 1, "login": 1 }, { unique: true });
db.contributors.createIndex({ "contributions": -1 });
db.contributors.createIndex({ "login": 1 });

db.topics.createIndex({ "name": 1 }, { unique: true });
db.topics.createIndex({ "repository_count": -1 });

// Create a user for the application (optional, for better security)
db.createUser({
  user: "github_analyzer",
  pwd: "analyzer_password",
  roles: [
    {
      role: "readWrite",
      db: "github_contributors"
    }
  ]
});

print("MongoDB initialization completed successfully!");
print("Created database: github_contributors");
print("Created collections: repositories, contributors, topics");
print("Created indexes for optimal query performance");
print("Created application user: github_analyzer");
