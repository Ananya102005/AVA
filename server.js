const express = require('express');
const path = require('path');
const bodyParser = require('body-parser');
const { exec } = require('child_process');
const app = express();
const port = process.env.PORT || 3000;
const fetch = require('node-fetch');

// Agent communication settings
const AGENT_API_URL = 'http://localhost:8002';
const STYLIST_AGENT_URL = 'http://localhost:6000';
let agentProcess = null;

// Middleware
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname, '/')));
app.use(express.urlencoded({ extended: true }));

// Log requests for debugging
app.use((req, res, next) => {
  console.log(`${req.method} ${req.path}`);
  next();
});

// Start agent function
function startAgent() {
  return new Promise((resolve, reject) => {
    console.log('Starting fetch.ai body scanner agent...');
    
    // Check if agent is already running
    agentProcess = exec('python run.py', (error, stdout, stderr) => {
      if (error) {
        console.error(`Agent process error: ${error}`);
        reject(new Error('Failed to start fetch.ai agent. Please make sure uagents is installed correctly.'));
        return;
      }
      console.log(`Agent stdout: ${stdout}`);
      if (stderr) {
        console.error(`Agent stderr: ${stderr}`);
      }
    });
    
    // Check if agent started successfully
    let retryCount = 0;
    const maxRetries = 5;
    const checkHealth = () => {
      console.log(`Attempting health check (attempt ${retryCount + 1}/${maxRetries})...`);
      fetch(`${AGENT_API_URL}/health`)
        .then(response => {
          if (response.ok) {
            console.log('Fetch.ai agent started successfully');
            resolve(true);
          } else {
            console.error('Fetch.ai agent returned non-200 status');
            retryOrFail();
          }
        })
        .catch(err => {
          console.error(`Couldn't connect to fetch.ai agent: ${err.message}`);
          retryOrFail();
        });
    };
    
    const retryOrFail = () => {
      retryCount++;
      if (retryCount < maxRetries) {
        console.log(`Retrying health check in 5 seconds...`);
        setTimeout(checkHealth, 5000); // Wait 5 seconds before retry
      } else {
        const error = new Error(`Could not connect to fetch.ai agent after ${maxRetries} attempts`);
        reject(error);
      }
    };
    
    // Initial health check after giving the agent time to start
    setTimeout(checkHealth, 10000); // Give agent 10 seconds to start initially
  });
}

// Add a banner to indicate this is using the fetch.ai agent
console.log("---------------------------------------------------------------");
console.log("AVA Style Assistant - Fetch.ai Agent Implementation with Gemini AI");
console.log("This application uses fetch.ai agents with Gemini AI for style analysis");
console.log("---------------------------------------------------------------");

// Helper function to communicate with the agent
async function callAgent(endpoint, data) {
  try {
    console.log(`Calling fetch.ai agent at ${AGENT_API_URL}${endpoint}...`);
    
    const response = await fetch(`${AGENT_API_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
      timeout: 10000 // 10 second timeout
    });
    
    if (!response.ok) {
      throw new Error(`Agent returned ${response.status}`);
    }
    
    const result = await response.json();
    console.log(`Agent response received: ${JSON.stringify(result)}`);
    return result;
  } catch (error) {
    console.error(`Error calling agent: ${error.message}`);
    throw error; // Re-throw to be handled by the caller
  }
}

// API Routes without local fallbacks
app.post('/api/analyze/body', async (req, res) => {
  try {
    const result = await callAgent('/analyze/body', req.body);
    res.json(result);
  } catch (error) {
    console.error(`Body analysis error: ${error.message}`);
    res.status(500).json({ 
      error: 'An error occurred during body shape analysis. Please try again later.' 
    });
  }
});

app.post('/api/analyze/face', async (req, res) => {
  try {
    const result = await callAgent('/analyze/face', req.body);
    res.json(result);
  } catch (error) {
    console.error(`Face analysis error: ${error.message}`);
    res.status(500).json({ 
      error: 'An error occurred during face shape analysis. Please try again later.' 
    });
  }
});

app.post('/api/analyze/color', async (req, res) => {
  try {
    const result = await callAgent('/analyze/color', req.body);
    res.json(result);
  } catch (error) {
    console.error(`Color analysis error: ${error.message}`);
    res.status(500).json({ 
      error: 'An error occurred during color analysis. Please try again later.' 
    });
  }
});

// Endpoints for retrieving type data for refine results
app.get('/api/analyze/body/type/:type', async (req, res) => {
  try {
    const bodyType = req.params.type;
    
    // Body type descriptions
    const bodyTypeData = {
      apple: {
        bodyType: 'apple',
        name: 'Apple',
        description: 'You have an "Apple" or "Circle" body shape, characterized by a fuller midsection, broader shoulders, and narrower hips. Your waist is less defined and you carry weight primarily around your midsection. Styling tips include clothing that creates a more defined waistline and draws attention to your legs and arms.'
      },
      triangle: {
        bodyType: 'triangle',
        name: 'Pear',
        description: 'You have a Triangle or "Pear" body shape, characterized by narrower shoulders compared to your hips, with your weight distributed more in your lower body. This is further emphasized by your self-described "bottom fit" and lower weight distribution.'
      },
      hourglass: {
        bodyType: 'hourglass',
        name: 'Hourglass',
        description: 'You have an Hourglass body shape, characterized by balanced shoulders and hips with a well-defined waist. Your proportions create the classic "figure-eight" silhouette. Clothing that highlights your waist and follows your natural curves will complement your shape beautifully.'
      },
      invertedTriangle: {
        bodyType: 'invertedTriangle',
        name: 'Inverted Triangle',
        description: 'You have an Inverted Triangle body shape, characterized by shoulders that are broader than your hips. You likely have an athletic build with well-defined shoulders and arms, and a less defined waist. Styling focuses on balancing your proportions by adding volume to your lower half.'
      },
      rectangle: {
        bodyType: 'rectangle',
        name: 'Rectangle',
        description: 'You have a Rectangle or "Straight" body shape, characterized by shoulders and hips that are approximately the same width, with little waist definition. Your weight is evenly distributed throughout your body, creating a straight up-and-down appearance. Styling can focus on creating the illusion of curves and definition.'
      }
    };
    
    // Return the data for the requested body type or a 404 if not found
    const data = bodyTypeData[bodyType];
    if (data) {
      res.json(data);
    } else {
      res.status(404).json({ error: 'Body type not found' });
    }
  } catch (error) {
    console.error(`Body type data error: ${error.message}`);
    res.status(500).json({ 
      error: 'An error occurred retrieving body type data.' 
    });
  }
});

app.get('/api/analyze/face/shape/:shape', async (req, res) => {
  try {
    const faceShape = req.params.shape;
    
    // Face shape descriptions
    const faceShapeData = {
      oval: {
        faceShape: 'oval',
        name: 'Oval',
        description: 'You have an Oval face shape, characterized by balanced proportions and a slightly curved jawline. This versatile face shape works well with most hairstyles and accessories. Your face is about one and a half times longer than it is wide, with a rounded hairline and jawline.'
      },
      round: {
        faceShape: 'round',
        name: 'Round',
        description: 'You have a Round face shape, characterized by soft angles, full cheeks, and equal width and length dimensions. Your face has a rounded chin and hairline, creating a circular appearance. Hairstyles with height and angles can help elongate your face.'
      },
      heart: {
        faceShape: 'heart',
        name: 'Heart',
        description: 'You have a Heart face shape, characterized by a wider forehead and narrower chin. Your face tapers from the forehead to the chin, creating an inverted triangle or heart-like shape. This shape often features a defined widow\'s peak and a pointed chin.'
      },
      square: {
        faceShape: 'square',
        name: 'Square',
        description: 'You have a Square face shape, characterized by a strong jawline and equally wide forehead. Your face has similar width and length measurements with angular features and a squared jawline. This shape conveys strength and can be softened with rounded hairstyles.'
      },
      diamond: {
        faceShape: 'diamond',
        name: 'Diamond',
        description: 'You have a Diamond face shape, characterized by pointed chin and forehead with the widest part at the cheekbones. Your face has angular features with narrow forehead and jawline, while the cheekbones are the most prominent feature.'
      },
      rectangle: {
        faceShape: 'rectangle',
        name: 'Rectangle',
        description: 'You have a Rectangle face shape, characterized by an elongated face with a forehead, cheekbones, and jawline of similar width. Your face is notably longer than it is wide, with a straight jawline and minimal curve at the chin. This elegant face shape benefits from hairstyles that add width and soften the angular lines.'
      }
    };
    
    // Return the data for the requested face shape or a 404 if not found
    const data = faceShapeData[faceShape];
    if (data) {
      res.json(data);
    } else {
      res.status(404).json({ error: 'Face shape not found' });
    }
  } catch (error) {
    console.error(`Face shape data error: ${error.message}`);
    res.status(500).json({ 
      error: 'An error occurred retrieving face shape data.' 
    });
  }
});

app.get('/api/analyze/color/season/:season', async (req, res) => {
  try {
    const colorSeason = req.params.season;
    
    // Color season descriptions
    const colorSeasonData = {
      winter: {
        colorSeason: 'winter',
        name: 'Winter',
        description: 'With your cool undertones and high contrast, you have a Winter color palette. Your coloring is best complemented by clear, crisp colors with blue undertones like pure white, navy blue, emerald green, and true red. Your color palette features deep, rich tones that create a dramatic effect with your high-contrast features.'
      },
      summer: {
        colorSeason: 'summer',
        name: 'Summer',
        description: 'With your cool undertones and soft contrast, you have a Summer color palette. Your coloring is best complemented by muted, cool-toned colors with blue undertones like lavender, dusty pink, slate blue, and soft navy. Avoid overly bright or warm colors.'
      },
      spring: {
        colorSeason: 'spring',
        name: 'Spring',
        description: 'Your warm undertones and medium contrast level indicate a Spring color palette. You look best in warm, clear colors with golden undertones like coral, peach, warm green, and golden yellow. Avoid dark or overly cool colors that can overwhelm your natural coloring.'
      },
      autumn: {
        colorSeason: 'autumn',
        name: 'Autumn',
        description: 'With your warm undertones and rich coloring, you have an Autumn color palette. You look best in warm, earthy tones with golden or orange undertones like terracotta, olive green, rust, and amber. Avoid clear, cool colors or pastels that clash with your rich coloring.'
      }
    };
    
    // Return the data for the requested color season or a 404 if not found
    const data = colorSeasonData[colorSeason];
    if (data) {
      res.json(data);
    } else {
      res.status(404).json({ error: 'Color season not found' });
    }
  } catch (error) {
    console.error(`Color season data error: ${error.message}`);
    res.status(500).json({ 
      error: 'An error occurred retrieving color season data.' 
    });
  }
});

// New Stylist Agent Endpoints
app.post('/api/stylist/recommendations', async (req, res) => {
  try {
    console.log("Received request for /api/stylist/recommendations");
    const userProfile = req.body.profile; // Expect profile data in the request body

    if (!userProfile) {
      return res.status(400).json({ error: 'User profile data is required.' });
    }

    console.log("User profile:", userProfile);

    // Call the Stylist Agent
    const response = await fetch(`${STYLIST_AGENT_URL}/`, { // POST to the root of the stylist agent
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ profile: userProfile }), // Send the profile
      timeout: 20000 // Increase timeout for potential AI generation
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`Stylist agent returned ${response.status}: ${errorText}`);
      throw new Error(`Stylist agent request failed with status ${response.status}`);
    }

    const result = await response.json();
    console.log("Stylist agent response:", result);
    res.json(result);

  } catch (error) {
    console.error(`Stylist recommendations error: ${error.message}`);
    res.status(500).json({
      error: 'An error occurred while fetching stylist recommendations. Please ensure the Stylist Agent is running.'
    });
  }
});

app.post('/api/stylist/search', async (req, res) => {
    try {
        console.log("Received request for /api/stylist/search");
        const { profile, searchQuery, occasion } = req.body; // Expect profile and query

        if (!profile) {
            return res.status(400).json({ error: 'User profile data is required.' });
        }

        console.log("User profile:", profile);
        console.log("Search query:", searchQuery);
        console.log("Occasion:", occasion);


        // Prepare data for Stylist Agent
        const requestData = {
            profile: profile,
            clothing_type: searchQuery || null, // Use searchQuery as clothing_type if provided
            occasion: occasion || null
        };

        // Call the Stylist Agent
        const response = await fetch(`${STYLIST_AGENT_URL}/`, { // POST to the root
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData),
            timeout: 20000 // Increase timeout
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Stylist agent search returned ${response.status}: ${errorText}`);
            throw new Error(`Stylist agent search request failed with status ${response.status}`);
        }

        const result = await response.json();
        console.log("Stylist agent search response:", result);

        // Note: The stylist agent filters based on clothing_type/occasion.
        // If we needed more specific keyword filtering *after* the agent call,
        // we would add it here by filtering `result.recommendations`.
        // For now, we return the agent's response directly.
        res.json(result);

    } catch (error) {
        console.error(`Stylist search error: ${error.message}`);
        res.status(500).json({
            error: 'An error occurred during the stylist search. Please ensure the Stylist Agent is running.'
        });
    }
});

// General form submission endpoint
app.post('/', (req, res) => {
  console.log('Form submission received:', req.body);
  res.redirect('/');
});

// Main route handler
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).send('Something broke! Please try again later.');
});

// Start the application
async function startApp() {
  try {
    // Start the agent
    await startAgent();
    
    // Start Express server
    app.listen(port, () => {
      console.log(`AVA Style Assistant is listening on port ${port}`);
      console.log(`Open http://localhost:${port} in your browser`);
    });
  } catch (error) {
    console.error('Failed to start application:', error);
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('Shutting down...');
  if (agentProcess) {
    agentProcess.kill();
  }
  process.exit(0);
});

// Start the application
startApp(); 