// netlify/functions/webhook-proxy.js

exports.handler = async function(event, context) {
  // Set CORS headers to allow requests from your domain
  const headers = {
    "Access-Control-Allow-Origin": "*", // In production, set this to your specific domain
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS"
  };
  
  // Handle preflight OPTIONS request
  if (event.httpMethod === "OPTIONS" ) {
    return {
      statusCode: 200,
      headers,
      body: ""
    };
  }
  
  // Only allow POST requests
  if (event.httpMethod !== "POST" ) {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ error: "Method not allowed" })
    };
  }
  
  try {
    // Parse the incoming request body
    const data = JSON.parse(event.body);
    
    // Log the data (optional)
    console.log("Received emotion data:", data);
    
    // Forward the request to n8n
    const n8nWebhookUrl = "https://mehax.app.n8n.cloud/webhook-test/https://ora-owjy.onrender.com/";
    
    const response = await fetch(n8nWebhookUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        emotion: data.emotion,
        confidence: data.confidence,
        timestamp: data.timestamp || new Date( ).toISOString(),
        text: data.text,
        sessionId: data.sessionId || "default"
      })
    });
    
    // Get the response from n8n
    const responseData = await response.text();
    
    // Return success response
    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        n8nResponse: responseData
      })
    };
  } catch (error) {
    console.error("Error:", error);
    
    // Return error response
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        success: false,
        error: error.message
      })
    };
  }
};
