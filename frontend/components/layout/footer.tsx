export function Footer() {
  return (
    <footer className="border-t border-white/[0.08] py-6 mt-8 transition-colors duration-200">
      <div className="max-w-[1200px] mx-auto px-8 text-center flex justify-center items-center gap-4 text-sm text-white/50">
        <p>&copy; {new Date().getFullYear()} AI Melody Generator</p>
        <span className="text-border dark:text-dark-border">|</span>
        <a
          href="https://github.com/niallone/melodygenerator"
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-indigo-400 transition-colors"
        >
          GitHub
        </a>
      </div>
    </footer>
  );
}
