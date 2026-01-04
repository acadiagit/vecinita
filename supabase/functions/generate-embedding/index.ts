// Supabase Edge Function for generating text embeddings
// Uses HuggingFace Inference API for sentence-transformers/all-MiniLM-L6-v2
// This eliminates the need for embedding models in the agent service

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// HuggingFace API configuration
const HF_API_URL = "https://api-inference.huggingface.co/pipeline/feature-extraction/sentence-transformers/all-MiniLM-L6-v2";
const HF_TOKEN = Deno.env.get('HUGGING_FACE_TOKEN');

if (!HF_TOKEN) {
  console.error('HUGGING_FACE_TOKEN environment variable not set');
}

interface EmbeddingRequest {
  text: string;
  texts?: string[];  // Batch support
}

async function generateEmbedding(text: string): Promise<number[]> {
  const response = await fetch(HF_API_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${HF_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      inputs: text,
      options: {
        wait_for_model: true,
      }
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`HuggingFace API error: ${response.status} - ${error}`);
  }

  const embedding = await response.json();
  
  // HF API returns array directly for single input
  if (Array.isArray(embedding) && typeof embedding[0] === 'number') {
    return embedding;
  }
  
  // Handle nested array format
  if (Array.isArray(embedding) && Array.isArray(embedding[0])) {
    return embedding[0];
  }
  
  throw new Error('Unexpected embedding format from HuggingFace API');
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const { text, texts }: EmbeddingRequest = await req.json();

    // Single text embedding
    if (text) {
      console.log(`Generating embedding for text (length: ${text.length})`);
      const embedding = await generateEmbedding(text);
      
      return new Response(
        JSON.stringify({ 
          embedding,
          dimension: embedding.length,
          model: 'sentence-transformers/all-MiniLM-L6-v2'
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200 
        }
      );
    }

    // Batch embedding support
    if (texts && Array.isArray(texts)) {
      console.log(`Generating embeddings for ${texts.length} texts`);
      const embeddings = await Promise.all(texts.map(t => generateEmbedding(t)));
      
      return new Response(
        JSON.stringify({ 
          embeddings,
          count: embeddings.length,
          dimension: embeddings[0]?.length,
          model: 'sentence-transformers/all-MiniLM-L6-v2'
        }),
        { 
          headers: { ...corsHeaders, 'Content-Type': 'application/json' },
          status: 200 
        }
      );
    }

    return new Response(
      JSON.stringify({ error: 'Missing "text" or "texts" parameter' }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 400 
      }
    );

  } catch (error) {
    console.error('Error generating embedding:', error);
    
    return new Response(
      JSON.stringify({ 
        error: error.message || 'Internal server error',
        details: error.toString()
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500 
      }
    );
  }
});
