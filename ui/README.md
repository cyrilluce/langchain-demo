# React TypeScript UI

React + TypeScript frontend for the LLM Agent demo, built with Vite and Bun.

## Features

- Modern React 18 with TypeScript
- Vite for fast development and building
- API integration with 6-minute timeout support
- Loading states and error handling
- Responsive design
- Real-time agent interaction

## Installation

### Prerequisites

- Bun (latest version) - Install from [bun.sh](https://bun.sh)
- Running FastAPI server on port 5001

### Setup

1. Install dependencies:

```bash
bun install
```

2. Verify server is running:

The UI expects the server to be available at http://localhost:5001

## Running the Application

### Development Mode

```bash
bun run dev
```

The application will be available at http://localhost:5173

### Build for Production

```bash
bun run build
```

Builds the app for production to the `dist/` folder.

### Preview Production Build

```bash
bun run preview
```

Locally preview the production build.

## Testing

Run tests with Vitest:

```bash
bun test
```

Run tests in watch mode:

```bash
bun test --watch
```

## Project Structure

```
ui/
├── src/
│   ├── App.tsx           # Main application component
│   ├── App.css           # Application styles
│   ├── main.tsx          # React entry point
│   ├── index.css         # Global styles
│   ├── services/
│   │   └── api.ts        # API client with timeout handling
│   └── types/
│       └── index.ts      # TypeScript type definitions
├── index.html            # HTML entry point
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
├── vite.config.ts        # Vite configuration
└── README.md            # This file
```

## Usage

1. Open http://localhost:5173 in your browser
2. Enter a prompt in the text area
3. Click "Submit" to send the request
4. Wait for the response (loading spinner appears)
5. View the agent's response or any errors

### Features

- **Long Request Support**: Automatically handles requests up to 6 minutes
- **Error Handling**: Clear error messages for timeouts, server errors, and validation
- **Loading States**: Visual feedback during request processing
- **Disabled Controls**: Form controls disabled during request to prevent duplicate submissions

## Configuration

### API Endpoint

The API base URL is configured in `src/services/api.ts`:

```typescript
const API_BASE_URL = 'http://localhost:5001';
```

To use a different server URL, update this constant.

### Timeout

The request timeout is set to 6 minutes (360000ms) in `src/services/api.ts`:

```typescript
const REQUEST_TIMEOUT = 360000; // 6 minutes
```

## Troubleshooting

### CORS Errors

If you see CORS errors in the browser console:
1. Ensure the FastAPI server is running
2. Verify the server has CORS middleware configured
3. Check that the API_BASE_URL matches your server address

### Connection Refused

If the UI can't connect to the server:
1. Verify the server is running: `curl http://localhost:5001/health`
2. Check the server port matches API_BASE_URL
3. Ensure no firewall is blocking the connection

### Build Errors

If you encounter build errors:

```bash
rm -rf node_modules bun.lockb
bun install
```

### TypeScript Errors

Ensure your TypeScript version is up to date:

```bash
bun update typescript
```

## Development

### Adding New Components

Create new components in `src/components/`:

```bash
mkdir -p src/components
```

### Styling

The app uses vanilla CSS. Styles are organized as:
- `index.css` - Global styles and CSS reset
- `App.css` - Component-specific styles

## Browser Support

- Modern evergreen browsers (Chrome, Firefox, Safari, Edge)
- ES2020+ JavaScript features
- CSS Grid and Flexbox

## License

See repository root for license information.
