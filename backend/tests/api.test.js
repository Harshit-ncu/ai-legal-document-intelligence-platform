const request = require('supertest');
const fs = require('fs');
const path = require('path');
const app = require('../src/app');

// Let's mock axios to simulate the external AI service calls
jest.mock('axios');
const axios = require('axios');

describe('Backend API Tests', () => {
  const testFilePath = path.join(__dirname, 'test.txt');
  const largeTestFilePath = path.join(__dirname, 'large.txt');
  const invalidFilePath = path.join(__dirname, 'test.exe');

  beforeAll(() => {
    // Create dummy files for upload
    fs.writeFileSync(testFilePath, 'This is a test file.');
    fs.writeFileSync(invalidFilePath, 'MZ...'); // Fake exe
    
    // Create a 6MB file for the size limit test
    const largeBuffer = Buffer.alloc(6 * 1024 * 1024, 'a');
    fs.writeFileSync(largeTestFilePath, largeBuffer);
  });

  afterAll(() => {
    // Cleanup dummy files
    if (fs.existsSync(testFilePath)) fs.unlinkSync(testFilePath);
    if (fs.existsSync(largeTestFilePath)) fs.unlinkSync(largeTestFilePath);
    if (fs.existsSync(invalidFilePath)) fs.unlinkSync(invalidFilePath);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('GET /health returns 200', async () => {
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ok');
  });

  test('GET /api/health returns 200', async () => {
    const res = await request(app).get('/api/health');
    expect(res.status).toBe(200);
    expect(res.body.status).toBe('ok');
  });

  test('Upload endpoint returns 200 on successful upload', async () => {
    // Mock the external FastAPI service to return a successful response
    axios.post.mockResolvedValueOnce({
      data: {
        success: true,
        text: 'Extracted text',
        documentType: 'TXT',
        classification: 'NDA',
        classificationConfidence: 0.9,
        ocrUsed: false,
        pageCount: 1,
        wordCount: 10,
        characterCount: 50,
        paragraphCount: 1,
        sentenceCount: 1,
        estimatedReadingTimeMinutes: 1,
        language: 'English',
        languageConfidence: 1,
        processingTimeMs: 100
      }
    });

    const res = await request(app)
      .post('/api/documents/upload')
      .attach('document', testFilePath);

    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.documentType).toBe('TXT');
  });

  test('Invalid file returns correct error (415)', async () => {
    const res = await request(app)
      .post('/api/documents/upload')
      .attach('document', invalidFilePath);

    // Multer or custom middleware throws an error for .exe
    expect(res.status).toBe(415);
    expect(res.body.success).toBe(false);
  });

  test('File larger than 5MB returns correct error (413)', async () => {
    const res = await request(app)
      .post('/api/documents/upload')
      .attach('document', largeTestFilePath);

    expect(res.status).toBe(413);
    expect(res.body.success).toBe(false);
  });

  test('AI service unavailable returns 503', async () => {
    // Mock ECONNREFUSED error from axios
    const error = new Error('connect ECONNREFUSED');
    error.code = 'ECONNREFUSED';
    axios.post.mockRejectedValueOnce(error);

    const res = await request(app)
      .post('/api/documents/upload')
      .attach('document', testFilePath);

    expect(res.status).toBe(503);
    expect(res.body.success).toBe(false);
    expect(res.body.error).toContain('AI Analysis Service is currently unavailable. Please try again later.');
  });
});
