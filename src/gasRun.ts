/* eslint-disable @typescript-eslint/no-namespace */
export declare namespace google {
  export namespace script {
    export interface IRun {
      getMarkDownFileList: (folderId: string) => void
      getMarkDownIndexFile: (folderId: string) => void
      withFailureHandler(callback: (error: Error, object?: unknown) => void): IRun

      // ジェネリック型Tを受け取り、より具体的な型情報をcallbackに提供
      withSuccessHandler<T>(callback: (value: T, object?: unknown) => void): IRun

      withUserObject(object: unknown): IRun
    }
    // eslint-disable-next-line init-declarations
    const run: IRun
  }
}

export type MarkDownList = { title: string; text: string }
function isMarkDownList(obj: unknown): obj is MarkDownList[] {
  if (Array.isArray(obj)) {
    return obj.every(
      (item) =>
        typeof item === 'object' &&
        item !== null &&
        'title' in item &&
        'text' in item &&
        typeof (item as MarkDownList).title === 'string' &&
        typeof (item as MarkDownList).text === 'string',
    )
  }
  return false
}
function isMarkDown(obj: unknown): obj is MarkDownList {
  if (Array.isArray(obj)) return false

  return (
    typeof obj == 'object' &&
    obj !== null &&
    'title' in obj &&
    'text' in obj &&
    typeof (obj as MarkDownList).title === 'string' &&
    typeof (obj as MarkDownList).text === 'string'
  )
}
export function fetchIndexFile(fileId: string): Promise<MarkDownList> {
  return new Promise((resolve, reject) => {
    google.script.run
      .withSuccessHandler<string>((result: string) => {
        try {
          const parsedResult: unknown = JSON.parse(result)
          if (isMarkDown(parsedResult)) {
            resolve(parsedResult)
          } else {
            throw new Error('Invalid response format')
          }
        } catch (e: unknown) {
          if (e instanceof Error) {
            reject(new Error(`戻り値が変: ${e.message}`))
          }
        }
      })
      .withFailureHandler(reject)
      .getMarkDownIndexFile(fileId)
  })
}

export function fetchFileList(folderId: string): Promise<MarkDownList[]> {
  return new Promise((resolve, reject) => {
    google.script.run
      .withSuccessHandler<string>((result: string) => {
        try {
          const parsedResult: unknown = JSON.parse(result)
          if (isMarkDownList(parsedResult)) {
            resolve(parsedResult)
          } else {
            throw new Error('Invalid response format')
          }
        } catch (e: unknown) {
          if (e instanceof Error) {
            reject(new Error(`戻り値が変: ${e.message}`))
          }
        }
      })
      .withFailureHandler(reject)
      .getMarkDownFileList(folderId)
  })
}
