import React, { useState } from 'react'
import { XMLParser } from 'fast-xml-parser'

const App: React.FC = () => {
  const [xmlContent, setXmlContent] = useState<string>('')
  const [parsedData, setParsedData] = useState<object | null>(null)

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (): void => {
        if (reader.result) {
          const xmlText = reader.result.toString()
          setXmlContent(xmlText)
          parseXml(xmlText)
        }
      }
      reader.readAsText(file)
    }
  }

  const parseXml = (xml: string): void => {
    const options = {
      ignoreAttributes: false,
      attributeNamePrefix: '@_',
      allowBooleanAttributes: true,
      parseAttributeValue: true,
      ignoreNameSpace: false,
    }
    const parser = new XMLParser(options)
    const result: unknown = parser.parse(xml)
    if (typeof result == 'object') {
      setParsedData(result)
    }
  }

  return (
    <div>
      <h1>XML Parser</h1>
      <input type='file' accept='.xml' onChange={handleFileChange} />
      {xmlContent && (
        <div>
          <h2>XML Content:</h2>
          <pre>{xmlContent}</pre>
        </div>
      )}
      {parsedData && (
        <div>
          <h2>Parsed Data:</h2>
          <pre>{JSON.stringify(parsedData, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}

export default App
