import { streamText } from 'ai';
import { config } from 'dotenv';

// Load .env.local first, then .env. This allows .env.local to override .env.
config({ path: '.env.local' });
config();

async function main() {
  console.log('🚀 Starting AI Gateway text generation...\n');

  const result = streamText({
    model: process.env.AI_MODEL || 'openai/gpt-5.4',
    prompt: 'Invent a new holiday and describe its traditions.',
    // AI Gateway automatically uses AI_GATEWAY_API_KEY from environment
  });

  // Stream the text response token by token
  process.stdout.write('📝 Response: ');
  for await (const textPart of result.textStream) {
    process.stdout.write(textPart);
  }

  console.log('\n');

  // Log token usage after streaming completes
  const usage = await result.usage;
  const finishReason = await result.finishReason;

  console.log('📊 Token usage:');
  console.log(`   • Prompt tokens:     ${usage.promptTokens}`);
  console.log(`   • Completion tokens: ${usage.completionTokens}`);
  console.log(`   • Total tokens:      ${usage.totalTokens}`);
  console.log(`\n✅ Finish reason: ${finishReason}`);
}

main().catch(console.error);
