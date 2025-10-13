'use client';

import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Loader2, FileText, Tag, Hash, BarChart3 } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

export default function Home() {
  const [text, setText] = useState('');
  const [texts, setTexts] = useState(['']);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const [preprocessOptions, setPreprocessOptions] = useState({
    lowercase: true,
    remove_punctuation: true,
    remove_numbers: false,
    remove_stopwords: true,
    stemming: false,
    lemmatization: false,
  });

  const API_URL = 'http://localhost:5000/api';

  const handlePreprocess = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/preprocess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, options: preprocessOptions }),
      });

      if (!response.ok) throw new Error('Failed to preprocess text');

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePOSTag = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/pos_tag`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, options: preprocessOptions }),
      });

      if (!response.ok) throw new Error('Failed to get POS tags');

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleBagOfWords = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const filteredTexts = texts.filter(t => t.trim() !== '');
      if (filteredTexts.length === 0) {
        throw new Error('Please provide at least one text');
      }

      const response = await fetch(`${API_URL}/bag_of_words`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texts: filteredTexts }),
      });

      if (!response.ok) throw new Error('Failed to create bag of words');

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTFIDF = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const filteredTexts = texts.filter(t => t.trim() !== '');
      if (filteredTexts.length === 0) {
        throw new Error('Please provide at least one text');
      }

      const response = await fetch(`${API_URL}/tfidf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texts: filteredTexts }),
      });

      if (!response.ok) throw new Error('Failed to calculate TF-IDF');

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const addTextInput = () => {
    setTexts([...texts, '']);
  };

  const updateTextInput = (index, value) => {
    const newTexts = [...texts];
    newTexts[index] = value;
    setTexts(newTexts);
  };

  const removeTextInput = (index) => {
    const newTexts = texts.filter((_, i) => i !== index);
    setTexts(newTexts.length === 0 ? [''] : newTexts);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="container mx-auto px-4 py-12 max-w-7xl">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-slate-900 to-slate-700 bg-clip-text text-transparent">
            NLP Text Preprocessing
          </h1>
          <p className="text-slate-600 text-lg">
            Advanced natural language processing tools for text analysis
          </p>
        </div>

        <Tabs defaultValue="preprocess" className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-8 h-auto">
            <TabsTrigger value="preprocess" className="flex items-center gap-2 py-3">
              <FileText className="w-4 h-4" />
              Preprocessing
            </TabsTrigger>
            <TabsTrigger value="pos" className="flex items-center gap-2 py-3">
              <Tag className="w-4 h-4" />
              POS Tagging
            </TabsTrigger>
            <TabsTrigger value="bow" className="flex items-center gap-2 py-3">
              <Hash className="w-4 h-4" />
              Bag of Words
            </TabsTrigger>
            <TabsTrigger value="tfidf" className="flex items-center gap-2 py-3">
              <BarChart3 className="w-4 h-4" />
              TF-IDF
            </TabsTrigger>
          </TabsList>

          <TabsContent value="preprocess">
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle>Text Preprocessing</CardTitle>
                <CardDescription>
                  Clean and normalize your text with various preprocessing options
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <Label htmlFor="text-input">Input Text</Label>
                  <Textarea
                    id="text-input"
                    placeholder="Enter your text here..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    className="min-h-32 mt-2"
                  />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-slate-50 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="lowercase"
                      checked={preprocessOptions.lowercase}
                      onCheckedChange={(checked) =>
                        setPreprocessOptions({ ...preprocessOptions, lowercase: checked })
                      }
                    />
                    <Label htmlFor="lowercase" className="cursor-pointer">Lowercase</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="punctuation"
                      checked={preprocessOptions.remove_punctuation}
                      onCheckedChange={(checked) =>
                        setPreprocessOptions({ ...preprocessOptions, remove_punctuation: checked })
                      }
                    />
                    <Label htmlFor="punctuation" className="cursor-pointer">Remove Punctuation</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="numbers"
                      checked={preprocessOptions.remove_numbers}
                      onCheckedChange={(checked) =>
                        setPreprocessOptions({ ...preprocessOptions, remove_numbers: checked })
                      }
                    />
                    <Label htmlFor="numbers" className="cursor-pointer">Remove Numbers</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="stopwords"
                      checked={preprocessOptions.remove_stopwords}
                      onCheckedChange={(checked) =>
                        setPreprocessOptions({ ...preprocessOptions, remove_stopwords: checked })
                      }
                    />
                    <Label htmlFor="stopwords" className="cursor-pointer">Remove Stopwords</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="stemming"
                      checked={preprocessOptions.stemming}
                      onCheckedChange={(checked) =>
                        setPreprocessOptions({ ...preprocessOptions, stemming: checked })
                      }
                    />
                    <Label htmlFor="stemming" className="cursor-pointer">Stemming</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="lemmatization"
                      checked={preprocessOptions.lemmatization}
                      onCheckedChange={(checked) =>
                        setPreprocessOptions({ ...preprocessOptions, lemmatization: checked })
                      }
                    />
                    <Label htmlFor="lemmatization" className="cursor-pointer">Lemmatization</Label>
                  </div>
                </div>

                <Button
                  onClick={handlePreprocess}
                  disabled={loading || !text.trim()}
                  className="w-full"
                  size="lg"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    'Preprocess Text'
                  )}
                </Button>

                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {result && (
                  <div className="space-y-4 p-4 bg-slate-50 rounded-lg">
                    <div>
                      <h3 className="font-semibold mb-2">Processing Steps:</h3>
                      <div className="flex flex-wrap gap-2">
                        {result.steps.map((step, idx) => (
                          <Badge key={idx} variant="secondary">{step}</Badge>
                        ))}
                      </div>
                    </div>
                    <div>
                      <h3 className="font-semibold mb-2">Original Text:</h3>
                      <p className="p-3 bg-white rounded border text-sm">{result.original}</p>
                    </div>
                    <div>
                      <h3 className="font-semibold mb-2">Processed Text:</h3>
                      <p className="p-3 bg-white rounded border text-sm">{result.processed}</p>
                    </div>
                    <div>
                      <h3 className="font-semibold mb-2">Tokens ({result.tokens.length}):</h3>
                      <div className="flex flex-wrap gap-2">
                        {result.tokens.map((token, idx) => (
                          <Badge key={idx}>{token}</Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="pos">
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle>Part-of-Speech Tagging</CardTitle>
                <CardDescription>
                  Identify the grammatical role of each word after preprocessing
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <Label htmlFor="pos-text">Input Text</Label>
                  <Textarea
                    id="pos-text"
                    placeholder="Enter your text here..."
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    className="min-h-32 mt-2"
                  />
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-4 bg-slate-50 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="pos-lowercase"
                      checked={preprocessOptions.lowercase}
                      onCheckedChange={(checked) =>
                        setPreprocessOptions({ ...preprocessOptions, lowercase: checked })
                      }
                    />
                    <Label htmlFor="pos-lowercase" className="cursor-pointer">Lowercase</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="pos-punctuation"
                      checked={preprocessOptions.remove_punctuation}
                      onCheckedChange={(checked) =>
                        setPreprocessOptions({ ...preprocessOptions, remove_punctuation: checked })
                      }
                    />
                    <Label htmlFor="pos-punctuation" className="cursor-pointer">Remove Punctuation</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="pos-numbers"
                      checked={preprocessOptions.remove_numbers}
                      onCheckedChange={(checked) =>
                        setPreprocessOptions({ ...preprocessOptions, remove_numbers: checked })
                      }
                    />
                    <Label htmlFor="pos-numbers" className="cursor-pointer">Remove Numbers</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="pos-stopwords"
                      checked={preprocessOptions.remove_stopwords}
                      onCheckedChange={(checked) =>
                        setPreprocessOptions({ ...preprocessOptions, remove_stopwords: checked })
                      }
                    />
                    <Label htmlFor="pos-stopwords" className="cursor-pointer">Remove Stopwords</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="pos-stemming"
                      checked={preprocessOptions.stemming}
                      onCheckedChange={(checked) =>
                        setPreprocessOptions({ ...preprocessOptions, stemming: checked })
                      }
                    />
                    <Label htmlFor="pos-stemming" className="cursor-pointer">Stemming</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="pos-lemmatization"
                      checked={preprocessOptions.lemmatization}
                      onCheckedChange={(checked) =>
                        setPreprocessOptions({ ...preprocessOptions, lemmatization: checked })
                      }
                    />
                    <Label htmlFor="pos-lemmatization" className="cursor-pointer">Lemmatization</Label>
                  </div>
                </div>

                <Button
                  onClick={handlePOSTag}
                  disabled={loading || !text.trim()}
                  className="w-full"
                  size="lg"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    'Analyze POS Tags'
                  )}
                </Button>

                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {result && result.pos_tags && (
                  <div className="space-y-4 p-4 bg-slate-50 rounded-lg">
                    {result.steps && (
                      <div>
                        <h3 className="font-semibold mb-2">Preprocessing Steps Applied:</h3>
                        <div className="flex flex-wrap gap-2">
                          {result.steps.map((step, idx) => (
                            <Badge key={idx} variant="secondary">{step}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    <div>
                      <h3 className="font-semibold mb-2">Original Text:</h3>
                      <p className="p-3 bg-white rounded border text-sm">{result.original}</p>
                    </div>
                    {result.preprocessed && (
                      <div>
                        <h3 className="font-semibold mb-2">Preprocessed Text:</h3>
                        <p className="p-3 bg-white rounded border text-sm">{result.preprocessed}</p>
                      </div>
                    )}
                    <div>
                      <h3 className="font-semibold mb-4">POS Tags:</h3>
                      <div className="space-y-2">
                        {result.pos_tags.map((item, idx) => (
                          <div key={idx} className="flex items-center gap-3 p-3 bg-white rounded border">
                            <span className="font-medium min-w-24">{item.word}</span>
                            <Badge variant="outline">{item.tag}</Badge>
                            <span className="text-sm text-slate-600">{item.explanation}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="bow">
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle>Bag of Words</CardTitle>
                <CardDescription>
                  Create a word frequency representation of your documents
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <Label>Input Texts</Label>
                  {texts.map((t, idx) => (
                    <div key={idx} className="flex gap-2">
                      <Textarea
                        placeholder={`Document ${idx + 1}...`}
                        value={t}
                        onChange={(e) => updateTextInput(idx, e.target.value)}
                        className="min-h-24"
                      />
                      {texts.length > 1 && (
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={() => removeTextInput(idx)}
                        >
                          ×
                        </Button>
                      )}
                    </div>
                  ))}
                  <Button variant="outline" onClick={addTextInput} className="w-full">
                    + Add Document
                  </Button>
                </div>

                <Button
                  onClick={handleBagOfWords}
                  disabled={loading}
                  className="w-full"
                  size="lg"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    'Create Bag of Words'
                  )}
                </Button>

                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {result && result.bow_dataframe && (
                  <div className="space-y-6 p-4 bg-slate-50 rounded-lg">
                    <div>
                      <h3 className="font-semibold mb-3">Vocabulary ({result.vocabulary_size} unique words)</h3>
                      <div className="overflow-x-auto bg-white rounded border">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              {result.vocabulary_columns.map((col) => (
                                <TableHead key={col} className="font-semibold">{col}</TableHead>
                              ))}
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {result.vocabulary_dataframe.map((row, idx) => (
                              <TableRow key={idx}>
                                {result.vocabulary_columns.map((col) => (
                                  <TableCell key={col}>{row[col]}</TableCell>
                                ))}
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold mb-3">Bag of Words Matrix</h3>
                      <div className="overflow-x-auto bg-white rounded border">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              {result.bow_columns.map((col) => (
                                <TableHead key={col} className="font-semibold">{col}</TableHead>
                              ))}
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {result.bow_dataframe.map((row, idx) => (
                              <TableRow key={idx}>
                                {result.bow_columns.map((col) => (
                                  <TableCell key={col} className={col === 'Document' ? 'font-medium' : ''}>
                                    {row[col]}
                                  </TableCell>
                                ))}
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold mb-2">Original Documents:</h3>
                      {result.original_texts.map((text, idx) => (
                        <div key={idx} className="p-3 bg-white rounded border mb-2">
                          <span className="font-medium">Doc {idx + 1}:</span> {text}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="tfidf">
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle>TF-IDF Analysis</CardTitle>
                <CardDescription>
                  Calculate Term Frequency-Inverse Document Frequency scores
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <Label>Input Texts</Label>
                  {texts.map((t, idx) => (
                    <div key={idx} className="flex gap-2">
                      <Textarea
                        placeholder={`Document ${idx + 1}...`}
                        value={t}
                        onChange={(e) => updateTextInput(idx, e.target.value)}
                        className="min-h-24"
                      />
                      {texts.length > 1 && (
                        <Button
                          variant="outline"
                          size="icon"
                          onClick={() => removeTextInput(idx)}
                        >
                          ×
                        </Button>
                      )}
                    </div>
                  ))}
                  <Button variant="outline" onClick={addTextInput} className="w-full">
                    + Add Document
                  </Button>
                </div>

                <Button
                  onClick={handleTFIDF}
                  disabled={loading}
                  className="w-full"
                  size="lg"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Calculating...
                    </>
                  ) : (
                    'Calculate TF-IDF'
                  )}
                </Button>

                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                {result && result.tfidf_dataframe && (
                  <div className="space-y-6 p-4 bg-slate-50 rounded-lg">
                    <div>
                      <h3 className="font-semibold mb-3">Vocabulary ({result.vocabulary_size} unique words)</h3>
                      <div className="overflow-x-auto bg-white rounded border">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              {result.vocabulary_columns.map((col) => (
                                <TableHead key={col} className="font-semibold">{col}</TableHead>
                              ))}
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {result.vocabulary_dataframe.map((row, idx) => (
                              <TableRow key={idx}>
                                {result.vocabulary_columns.map((col) => (
                                  <TableCell key={col}>{row[col]}</TableCell>
                                ))}
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold mb-3">TF-IDF Matrix</h3>
                      <div className="overflow-x-auto bg-white rounded border">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              {result.tfidf_columns.map((col) => (
                                <TableHead key={col} className="font-semibold">{col}</TableHead>
                              ))}
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {result.tfidf_dataframe.map((row, idx) => (
                              <TableRow key={idx}>
                                {result.tfidf_columns.map((col) => (
                                  <TableCell key={col} className={col === 'Document' ? 'font-medium' : ''}>
                                    {row[col]}
                                  </TableCell>
                                ))}
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold mb-2">Original Documents:</h3>
                      {result.original_texts.map((text, idx) => (
                        <div key={idx} className="p-3 bg-white rounded border mb-2">
                          <span className="font-medium">Doc {idx + 1}:</span> {text}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        
      </div>
    </div>
  );
}
