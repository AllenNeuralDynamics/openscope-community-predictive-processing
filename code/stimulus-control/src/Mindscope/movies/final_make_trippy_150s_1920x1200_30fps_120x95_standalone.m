function final_make_trippy_150s_1920x1200_30fps_120x95_standalone
% Standalone reimplementation of:
% https://github.com/cajal/pipeline/blob/master/matlab/schemas/%2Bvis/Trippy.m
% without DataJoint.
% Produces: 10 × 15 s trials concatenated (2.5 min) at 1920×1200 @ 30 fps.
% Seeds per trial: 1..10. FoV = [120 95] degrees.
%
% IMPORTANT for pixel identity:
% - Use the same functions and call order as Trippy.m.
% - Write frames as DOUBLE in [0,1] (no uint8 rounding).
% NOTE: Requires Signal Processing Toolbox (hanning, gausswin).

% -----------------------
% Output & display params
% -----------------------
outfile   = 'trippy_150s_1920x1200_30fps_120x95.mp4';
tex_xdim  = 1920;
tex_ydim  = 1200;
fps       = 30;

trials          = 10;    % 10 × 15 s
trial_duration  = 15;    % seconds per trial
seed0           = 1;     % seeds 1..10

% -----------------------
% Trippy "cond" parameters (Version 1)
% -----------------------
cond.version              = 1;        % not used numerically
cond.rng_seed             = [];       % set per trial
cond.luminance            = 0.5;      % not used in math here
cond.contrast             = 1.0;      % Michelson
cond.tex_ydim             = tex_ydim;
cond.tex_xdim             = tex_xdim;
cond.duration             = [];       % set per trial
cond.frame_downsample     = 2;        % not used here (we fix fps)
cond.xnodes               = 8;
cond.ynodes               = 6;
cond.temp_freq            = 4.0;      % Hz
cond.temp_kernel_length   = 61;       % odd >= 3
cond.spatial_freq         = 0.06;     % cy/deg

screen_deg = [120 95];   % [deg_x deg_y]

% Auto up_factor (MUST be wide enough; 240 here)
cond.up_factor = ceil(max(cond.tex_xdim/cond.xnodes, cond.tex_ydim/cond.ynodes));  % → 240

% -----------------------
% Video writer (tune size via Quality)
% -----------------------
vw = VideoWriter(outfile, 'MPEG-4');
vw.FrameRate = fps;
vw.Quality   = 19;   % adjust as needed
open(vw);

% Luminance mapping: movie = cos(2*pi*phase)/2 + 1/2 (double)
total_frames = trials * ceil(trial_duration * fps);
fprintf('Rendering %s  (%dx%d @ %g fps, %d frames)\n', outfile, tex_xdim, tex_ydim, fps, total_frames);

frames_done = 0;

for t = 1:trials
    % Per-trial seed and duration
    cond.rng_seed = (seed0 + (t - 1));
    cond.duration = trial_duration;

    % 1) packed phase movie (low-res, double)
    phase_packed = make_packed_phase_movie(cond, fps, screen_deg);

    % 2) temporal interpolation (double): upsample + Hann + linear drift
    phase_time = interp_time(phase_packed, cond, fps);

    % 3) spatial interpolation (double): frozen two-pass Gaussian upscaler
    phase_full = interp_space(phase_time, cond);  % [tex_ydim × tex_xdim × T], double

    % 4) cosine luminance map (double in [0,1]) and write
    T = size(phase_full, 3);
    for f = 1:T
        phase_frame = phase_full(:,:,f);      % double (cycles)
        lumin = cos(2*pi*phase_frame)/2 + 1/2; % double in [0,1], as in original

        % Write as double grayscale; some systems may need 3-ch fallback:
        try
            writeVideo(vw, lumin);
        catch
            writeVideo(vw, repmat(lumin, [1 1 3]));
        end

        frames_done = frames_done + 1;
        if mod(frames_done, max(1, floor(total_frames/10))) == 0
            fprintf('  %3.0f%%\n', 100*frames_done/total_frames);
        end
    end
end

close(vw);
fprintf('Done. Wrote %s\n', outfile);

% ======================================================================
% Faithful reimplementations of +vis/Trippy.m (Version 1) static methods
% ======================================================================

function phase = make_packed_phase_movie(cond, fps_in, degxy)
    % Make compressed phase movie. (double, like original)
    r = RandStream.create('mt19937ar','Seed', cond.rng_seed);
    nframes = ceil(cond.duration * fps_in);
    n = [cond.ynodes cond.xnodes];
    k = cond.temp_kernel_length;
    assert(k>=3 && mod(k,2)==1, 'temp_kernel_length must be odd >= 3');
    k2 = ceil(k/4);
    compensator = 8.0;
    scale = compensator * cond.up_factor * cond.spatial_freq * degxy(1) / cond.tex_xdim;
    phase = scale * r.rand(ceil((nframes + k - 1)/k2), prod(n));  % double
end

function phase = interp_time(phase, cond, fps_in)
    nframes = ceil(cond.duration * fps_in);

    % lowpass in time (double)
    k = cond.temp_kernel_length;
    assert(k>=3 && mod(k,2)==1, 'temp_kernel_length must be odd >= 3');
    k2 = ceil(k/4);
    phase = upsample(phase, k2);                  % zero insertion along rows
    tempKernel = hanning(k);                      % Signal Toolbox hanning()
    tempKernel = (k2 / sum(tempKernel)) * tempKernel;
    phase = conv2(phase, tempKernel, 'valid');    % lowpass in time
    phase = phase(1:nframes, :);

    % add motion (linear drift in cycles/s), original uses bsxfun
    phase = bsxfun(@plus, phase, ((1:nframes)'/fps_in) * cond.temp_freq);
end

function movie = interp_space(phase, cond)
    % upscale to full size (double)
    n = [cond.ynodes cond.xnodes];
    f = cond.up_factor;
    T = size(phase,1);
    movie_up = zeros(n(1)*f, n(2)*f, T);
    for i = 1:T
        frame_low = reshape(phase(i,:), n);
        movie_up(:,:,i) = frozen_upscale(frame_low, f);
    end
    % crop to requested texture size
    movie = movie_up(1:cond.tex_ydim, 1:cond.tex_xdim, :);
end

function img = frozen_upscale(img, factor)
    % Frozen on 2015-12-30 — do not alter (matches original math).
    for i = 1:2
        img = upsample(img', factor, round(factor/2));  % transpose + phased insertion
        L = size(img,1);
        k = gausswin(L, sqrt(0.5)*L/factor);            % Signal Toolbox
        k = ifftshift((factor/sum(k)) * k);
        img = real(ifft(bsxfun(@times, fft(img), fft(k))));
    end
end

end
