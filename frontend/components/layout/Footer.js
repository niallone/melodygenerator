export function Footer() {
  return (
    <footer className="bg-light-gray text-dark-gray py-4 mt-8">
      <div className="max-w-[1200px] mx-auto px-8 text-center flex justify-center items-center gap-4">
        <p>&copy; {new Date().getFullYear()} AI Melody Generator.</p>
        <a
          href="https://github.com/niallone/melodygenerator"
          target="_blank"
          rel="noopener noreferrer"
          className="no-underline text-dark-gray flex items-center gap-2 hover:underline"
        >
          GitHub
        </a>
      </div>
    </footer>
  );
}
