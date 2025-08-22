import React from 'react';
import Papa from 'papaparse';

interface ParsedFile {
  name: string;
  data: Record<string, unknown>[];
}

interface WizardUploadProps {
  setData: (data: ParsedFile[]) => void;
}

export default function WizardUpload({ setData }: WizardUploadProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    const parsed: ParsedFile[] = new Array(files.length);
    let remaining = files.length;
    Array.from(files).forEach((file, index) => {
      Papa.parse<Record<string, unknown>>(file, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          parsed[index] = { name: file.name, data: results.data };
          remaining -= 1;
          if (remaining === 0) {
            setData(parsed);
            localStorage.setItem('wizardUpload', JSON.stringify(parsed));
          }
        }
      });
    });
  };

  return (
    <input
      type="file"
      accept=".csv"
      multiple
      data-testid="wizard-upload-input"
      onChange={handleChange}
    />
  );
}

