const { OpenFgaApi, Configuration } = require('@openfga/sdk');

// Configuration
const config = {
  apiUrl: process.env.FGA_API_URL || 'http://localhost:8080',
  storeId: process.env.FGA_STORE_ID,
  authorizationModelId: process.env.FGA_AUTHORIZATION_MODEL_ID,
  apiToken: process.env.FGA_API_TOKEN
};

// Initialize OpenFGA client
const fga = new OpenFgaApi(new Configuration({
  apiUrl: config.apiUrl,
  credentials: {
    method: 'api_token',
    token: config.apiToken
  }
}));

// Authorization model for the RAG demo
const authorizationModel = {
  schema_version: "1.1",
  type_definitions: [
    {
      type: "user",
      relations: {}
    },
    {
      type: "doc",
      relations: {
        viewer: {
          union: {
            child: [
              {
                _this: {}
              }
            ]
          }
        }
      }
    }
  ]
};

async function setupOpenFGA() {
  try {
    console.log('🚀 Setting up OpenFGA for FGA-Secured RAG Demo...');
    
    // Step 1: Create authorization model
    console.log('📝 Creating authorization model...');
    const modelResponse = await fga.writeAuthorizationModel({
      body: {
        schema_version: authorizationModel.schema_version,
        type_definitions: authorizationModel.type_definitions
      }
    });
    
    console.log(`✅ Authorization model created with ID: ${modelResponse.authorization_model_id}`);
    
    // Step 2: Set up demo permissions
    console.log('🔐 Setting up demo permissions...');
    
    // Intern Ashish can only view marketing document
    await fga.write({
      body: {
        writes: {
          tuple_keys: [
            {
              user: "user:intern_ashish",
              relation: "viewer",
              object: "doc:titan_marketing"
            }
          ]
        }
      }
    });
    
    // PM Kate can view both documents
    await fga.write({
      body: {
        writes: {
          tuple_keys: [
            {
              user: "user:pm_kate",
              relation: "viewer",
              object: "doc:titan_marketing"
            },
            {
              user: "user:pm_kate",
              relation: "viewer",
              object: "doc:titan_spec"
            }
          ]
        }
      }
    });
    
    console.log('✅ Demo permissions set up successfully!');
    
    // Step 3: Display configuration info
    console.log('\n📋 Configuration Summary:');
    console.log(`Store ID: ${config.storeId}`);
    console.log(`Authorization Model ID: ${modelResponse.authorization_model_id}`);
    console.log(`API URL: ${config.apiUrl}`);
    
    console.log('\n🔑 Demo Users:');
    console.log('- intern_ashish: Can view titan_marketing only');
    console.log('- pm_kate: Can view both titan_marketing and titan_spec');
    
    console.log('\n📄 Demo Documents:');
    console.log('- titan_marketing: Public marketing brief');
    console.log('- titan_spec: Confidential engineering specs with budget info');
    
    console.log('\n🎯 Test the demo by asking: "What is the budget for Project Titan?"');
    console.log('Switch between users to see different responses based on permissions!');
    
  } catch (error) {
    console.error('❌ Error setting up OpenFGA:', error.message);
    if (error.response) {
      console.error('Response details:', error.response.data);
    }
    process.exit(1);
  }
}

// Run setup if this script is executed directly
if (require.main === module) {
  setupOpenFGA();
}

module.exports = { setupOpenFGA, authorizationModel }; 