Name:           persiantypefixer
Version:        %{app_version}
Release:        1
Summary:        Persian and English keyboard layout fixer
License:        MIT
URL:            https://github.com/salehghotbani/PersianTypeFixer
Packager:       Seyed Mohammad Saleh Ghotbani
ExclusiveArch:  x86_64
AutoReqProv:    no
Requires:       ca-certificates, dejavu-sans-fonts, dbus-libs, fontconfig, glib2, openssl-libs
Requires:       libglvnd-egl, libglvnd-glx, libX11, libXext, libXrender, libICE, libSM, libxcb
Requires:       xcb-util-cursor, xcb-util-image, xcb-util-keysyms, xcb-util-renderutil, xcb-util-wm
Requires:       libxkbcommon, libxkbcommon-x11, xkeyboard-config
Requires:       libwayland-client.so.0()(64bit), libwayland-cursor.so.0()(64bit), libwayland-egl.so.1()(64bit)

# The PyInstaller payload is already linked and stripped as needed.
%define __os_install_post %{nil}
%global debug_package %{nil}

%description
Correct selected text typed with the wrong keyboard layout in an X11 or
compatible Wayland desktop session.

%install
mkdir -p "%{buildroot}"
cp -a "%{app_payload}/." "%{buildroot}/"

%files
/opt/persiantypefixer
/usr/share/applications/ir.ghotbani.persiantypefixer.desktop
/usr/share/icons/hicolor/scalable/apps/ir.ghotbani.persiantypefixer.svg
%license /usr/share/doc/persiantypefixer/copyright
%doc /usr/share/doc/persiantypefixer/THIRD_PARTY_NOTICES.md
