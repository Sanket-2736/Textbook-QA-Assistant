# Textbook Q&A RAG - Frontend

React + Vite + Tailwind CSS frontend for the Interactive Textbook Q&A RAG System.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run development server:
   ```bash
   npm run dev
   ```

   The app will open at `http://localhost:5173`

## Build

To build for production:
```bash
npm run build
```

The build output will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── main.jsx          # Entry point
│   ├── App.jsx           # Root component
│   ├── App.css           # Styling
│   └── components/       # Reusable components
├── index.html            # HTML template
├── vite.config.js        # Vite configuration
├── tailwind.config.js    # Tailwind configuration
├── postcss.config.js     # PostCSS configuration
├── package.json          # Dependencies and scripts
└── README.md             # This file
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally

## Technologies

- **React 18** - UI library
- **Vite 5** - Frontend tooling
- **Tailwind CSS** - Utility-first CSS framework
- **PostCSS** - CSS transformations
- **Autoprefixer** - Browser compatibility

## Environment Variables

Create a `.env.local` file in the frontend root:

```env
VITE_API_URL=http://localhost:8000
```

Access in React components with `import.meta.env.VITE_API_URL`.
