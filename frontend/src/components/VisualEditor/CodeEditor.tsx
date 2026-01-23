import React, { useRef, useEffect } from 'react';
import Editor, { OnMount } from "@monaco-editor/react";

interface CodeEditorProps {
    code: string;
    language: string;
    onChange: (value: string | undefined) => void;
    readOnly?: boolean;
}

const CodeEditor: React.FC<CodeEditorProps> = ({ code, language, onChange, readOnly = false }) => {
    const editorRef = useRef(null);

    const handleEditorDidMount: OnMount = (editor, monaco) => {
        editorRef.current = editor;
    };

    return (
        <Editor
            height="100%"
            defaultLanguage={language}
            value={code} // Controlled by parent
            theme="vs-dark"
            onChange={onChange}
            onMount={handleEditorDidMount}
            options={{
                readOnly,
                minimap: { enabled: false },
                fontSize: 14,
                wordWrap: 'on',
                scrollBeyondLastLine: false,
                automaticLayout: true,
            }}
        />
    );
};

export default CodeEditor;
