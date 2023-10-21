import { useEffect, useState } from "react";
import "./App.css";

const DEFAULT_CHANNELS: string[] = [
  "hey",
  "you",
  "there",
  JSON.stringify({ a: 1, b: 2 }, null, 2),
];

function App() {
  const serverUrl = "https://localhost:1234";
  const [channels, setChannels] = useState(DEFAULT_CHANNELS);
  const [pageErrors, setPageErrors] = useState(null);
  useEffect(() => {
    let ignore = false;
    setChannels([]);
    fetch(serverUrl)
      .then((res) => res.json())
      .then(
        (result) => {
          if (!ignore) {
            setChannels(result);
          }
        },
        (error) => {
          setChannels(DEFAULT_CHANNELS);
          setPageErrors(error.message);
        }
      );
    return () => {
      ignore = true;
    };
  }, [serverUrl]);

  const channelList = (channels: string[] = DEFAULT_CHANNELS) => {
    return (
      <>
        {channels.map((data) => {
          return <div className="channel">{data as string}</div>;
        })}
      </>
    );
  };
  return (
    <div className="App">
      <h1>Yarkie</h1>
      {pageErrors && <div className="error">Error: {pageErrors}</div>}
      {channels.length == 0 && <div className="empty">No channels found</div>}
      {channels.length > 0 && channelList(channels)}
    </div>
  );
}

export default App;
