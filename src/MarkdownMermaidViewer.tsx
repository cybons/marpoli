import React, { useState, useEffect } from 'react'
import { marked } from 'marked'
import mermaid from 'mermaid'
import './MarkdownMermaidViewer.css'
import { fetchFileList, fetchIndexFile, MarkDownList } from './gasRun'

const MarkdownMermaidViewer = (): JSX.Element => {
  const [htmlContent, setHtmlContent] = useState('')
  const [files, setFiles] = useState<MarkDownList[]>([])
  const [currentFile, setCurrentFile] = useState<string>('')

  const loadMarkdownFile = async (fileId: string): Promise<void> => {
    const content = await fetchIndexFile(fileId)
    const renderer = new marked.Renderer()
    renderer.code = (code, language): string => {
      if (language === 'mermaid') {
        return `<div class="mermaid">${code}</div>`
      } else {
        return `<pre><code>${code}</code></pre>`
      }
    }
    marked.setOptions({ renderer })
    const html = await marked.parse(content.text)
    setHtmlContent(html)
    setCurrentFile(fileId)

    mermaid.run({ suppressErrors: true })
    mermaid.contentLoaded()
  }

  const fetchMarkdownFiles = async (folder_id: string): Promise<void> => {
    const markdownList = await fetchFileList(folder_id)
    setFiles(markdownList)
  }

  useEffect(() => {
    fetchMarkdownFiles('YOUR_FOLDER_ID')
    loadMarkdownFile('YOUR_INITIAL_FILE_ID') // 初期表示するファイルの ID を設定
  }, [])

  return (
    <div className='markdown-container'>
      <p>{currentFile}</p>
      <nav>
        <ul>
          {files.map((file) => (
            <li key={file.text}>
              <button onClick={() => loadMarkdownFile(file.text)}>{file.title}</button>
            </li>
          ))}
        </ul>
      </nav>
      <div dangerouslySetInnerHTML={{ __html: htmlContent }} />
    </div>
  )
}

export default MarkdownMermaidViewer
