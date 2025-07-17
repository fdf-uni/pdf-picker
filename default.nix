{
  lib,
  python3Packages,
  fetchFromGitHub,
}:

python3Packages.buildPythonApplication rec {
  pname = "pdf-picker";
  version = "0.1.3";
  pyproject = true;

  src = fetchFromGitHub {
    owner = "fdf-uni";
    repo = "pdf-picker";
    rev = "v${version}";
    hash = "sha256-+hzL1YoRpph9QlBvTU9LmciwV3uHyrmnNIypXg2ei9s=";
  };

  build-system = with python3Packages; [
    hatchling
  ];

  dependencies = with python3Packages; [
    pymupdf
  ];

  pythonImportsCheck = [ "pdf_picker" ];

  meta = {
    description = "Interactively open a PDF file, optionally at a specific TOC entry.";
    mainProgram = "pdf-picker";
    homepage = "https://github.com/fdf-uni/pdf-picker";
    license = lib.licenses.mit;
  };
}
