import React, { useState } from 'react';
import Button from './Button';

export default function ActionBar() {
  const [rfqRaised, setRfqRaised] = useState(false);
  const [pickListIssued, setPickListIssued] = useState(false);
  const [parked, setParked] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const raiseRFQ = () => {
    setRfqRaised(true);
    setToast('RFQ raised');
  };

  const issuePickList = () => {
    setPickListIssued(true);
    setToast('Pick list issued');
  };

  const parkWo = () => {
    setParked(true);
    setToast('Work order parked');
  };

  const unparkWo = () => {
    setParked(false);
    setToast('Work order unparked');
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        <Button aria-label="Raise RFQ" onClick={raiseRFQ} disabled={rfqRaised}>
          Raise RFQ
        </Button>
        <Button aria-label="Issue pick list" onClick={issuePickList} disabled={pickListIssued}>
          Issue pick list
        </Button>
        {!parked ? (
          <Button aria-label="Park WO" onClick={parkWo}>
            Park WO
          </Button>
        ) : (
          <Button aria-label="Unpark" onClick={unparkWo}>
            Unpark
          </Button>
        )}
      </div>
      {toast && (
        <div role="status" aria-live="polite" className="text-sm">
          {toast}
        </div>
      )}
    </div>
  );
}

