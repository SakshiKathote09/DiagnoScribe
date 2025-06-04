import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const App = () => {
  const [transcript, setTranscript] = useState('');
  const [audioFile, setAudioFile] = useState(null);
  const [documentation, setDocumentation] = useState({});
  const [errors, setErrors] = useState({});
  const [elements, setElements] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    // Fetch documentation elements
    axios.get('http://localhost:8000/elements')
      .then(response => setElements(response.data))
      .catch(error => {
        console.error('Error fetching elements:', error);
        setErrorMessage('Failed to fetch documentation elements.');
      });
  }, []);

  const handleAudioUpload = async () => {
    if (!audioFile) return;
    setLoading(true);
    setErrorMessage('');
    const formData = new FormData();
    formData.append('file', audioFile);
    
    try {
      const response = await axios.post('http://localhost:8000/transcribe', formData);
      setTranscript(response.data.transcript);
    } catch (error) {
      console.error('Error transcribing audio:', error);
      setErrorMessage('Failed to transcribe audio. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDocumentation = async () => {
    setLoading(true);
    setErrorMessage('');
    try {
      const response = await axios.post('http://localhost:8000/generate_documentation', { transcript });
      setDocumentation(response.data.elements);
      setErrors(response.data.errors);
    } catch (error) {
      console.error('Error generating documentation:', error);
      setErrorMessage('Failed to generate documentation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setTranscript('');
    setAudioFile(null);
    setDocumentation({});
    setErrors({});
    setErrorMessage('');
  };

  const renderElement = (element, data, error) => {
    if (error) {
      return <p className="text-red-500">Error: {error}</p>;
    }
    if (!data) {
      return <p>No data available for this element.</p>;
    }

    try {
      switch (element.display_format.type) {
        case 'text':
          return <p>{data[element.display_format.field]}</p>;
        case 'list':
          const listField = element.display_format.fields[0];
          if (!data[listField] || !Array.isArray(data[listField])) {
            return <p className="text-yellow-500">Invalid data format: Expected a list for {listField}.</p>;
          }
          return (
            <ul>
              {data[listField].map(item => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          );
        case 'table':
          return (
            <table className="table-auto w-full">
              <thead>
                <tr>
                  {element.display_format.fields.map(field => (
                    <th key={field} className="px-4 py-2">{field}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  {element.display_format.fields.map(field => (
                    <td key={field} className="border px-4 py-2">{data[field] || 'N/A'}</td>
                  ))}
                </tr>
              </tbody>
            </table>
          );
        default:
          return <p>Unsupported format</p>;
      }
    } catch (e) {
      console.error(`Error rendering element ${element.name}:`, e);
      return <p className="text-red-500">Error rendering data: {e.message}</p>;
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-4">Cliniscribe Documentation System</h1>
      
      {errorMessage && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {errorMessage}
        </div>
      )}

      <div className="mb-4">
        <h2 className="text-xl font-semibold">Upload Audio</h2>
        <input
          type="file"
          accept="audio/*"
          onChange={e => setAudioFile(e.target.files[0])}
          className="mb-2"
        />
        <div className="flex space-x-2">
          <button
            onClick={handleAudioUpload}
            disabled={loading || !audioFile}
            className="bg-blue-500 text-white px-4 py-2 rounded disabled:bg-gray-400"
          >
            {loading ? 'Transcribing...' : 'Transcribe Audio'}
          </button>
          <button
            onClick={handleClear}
            className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
          >
            Clear
          </button>
        </div>
      </div>

      <div className="mb-4">
        <h2 className="text-xl font-semibold">Transcript</h2>
        <textarea
          value={transcript}
          onChange={e => setTranscript(e.target.value)}
          className="w-full h-32 p-2 border rounded"
          placeholder="Enter or edit transcript here"
        />
        <div className="flex space-x-2">
          <button
            onClick={handleGenerateDocumentation}
            disabled={loading || !transcript}
            className="bg-green-500 text-white px-4 py-2 rounded disabled:bg-gray-400"
          >
            {loading ? 'Generating...' : 'Generate Documentation'}
          </button>
          <button
            onClick={handleClear}
            className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
          >
            Clear
          </button>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold">Documentation</h2>
        {elements.map(element => (
          <div key={element.id} className="mb-4 p-4 border rounded">
            <h3 className="text-lg font-medium">{element.name}</h3>
            <p className="text-gray-600">{element.description}</p>
            {renderElement(element, documentation[element.id], errors[element.id])}
          </div>
        ))}
      </div>
    </div>
  );
};

export default App;