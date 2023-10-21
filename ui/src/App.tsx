import { useEffect, useState } from "react";
import "./App.css";

const DEFAULT_PLAYLISTS: string[] = [
  "hey",
  "you",
  "there",
  JSON.stringify({ a: 1, b: 2 }, null, 2),
];

function App() {
  const serverUrl = "https://localhost:1234";
  const [playlists, setPlaylists] = useState(DEFAULT_PLAYLISTS);
  const [pageErrors, setPageErrors] = useState(null);
  useEffect(() => {
    let ignore = false;
    setPlaylists([]);
    fetch(serverUrl)
      .then((res) => res.json())
      .then(
        (result) => {
          if (!ignore) {
            setPlaylists(result);
          }
        },
        (error) => {
          setPlaylists(DEFAULT_PLAYLISTS);
          setPageErrors(error.message);
        }
      );
    return () => {
      ignore = true;
    };
  }, [serverUrl]);

  const playlistsList = (items: string[] = DEFAULT_PLAYLISTS) => {
    return (
      <>
        {items.map((data) => {
          return <div className="playlist">{data as string}</div>;
        })}
      </>
    );
  };
  return (
    <div className="App">
      <h1>Yarkie</h1>
      {pageErrors && <div className="error">Error: {pageErrors}</div>}
      {playlists.length == 0 && <div className="empty">No channels found</div>}
      {playlists.length > 0 && playlistsList(playlists)}
    </div>
  );
}

export default App;
