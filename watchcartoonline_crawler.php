<?php
    
    // Logging settings
    class Log {
        const ERR = 0;
        const WARN = 1;
        const DEBUG = 2;
    }
    
    // Global vars
    $CACHE_DIR = "cache_watchcartoononline";
    
    // Regex Strings
	$REGEX_NEXT = '/href=\"([^"]+)\" rel=\"next\"/';
	$REGEX_VIDEO = '/v=([^&"]+)/';
    $REGEX_THUMBNAIL = '/image=([^&"]+)/';
    $REGEX_EPISODE = '/[Ss]eason.\d+.[Ee]pisode.(\d+)/';
    $REGEX_SEASON = '/[Ss]eason.(\d+).[Ee]pisode.\d+/';
    
    // The page we want to request
    //$current = "http://www.watchcartoononline.com/the-simpsons-episode-101-simpsons-roasting";
    //$current = "http://www.watchcartoononline.com/the-simpsons-season-7-episode-1-who-shot-mr-burns-part-two";
    //$current = "http://www.watchcartoononline.com/the-simpsons-season-8-episode-1-treehouse-of-horror-vii";
    //$current = "http://www.watchcartoononline.com/the-simpsons-season-9-episode-1-%E2%80%93-the-city-of-new-york-vs-homer-simpson";
    $current = "http://www.watchcartoononline.com/the-simpsons-season-16-episode-1-treehouse-of-horror-xv";
    $season = 16;
    
    do {
        // Outer loop so that it doesn't stop between seasons
        $ep = 1;

        while (isset($current)) {
            // See if we already have it in our cache (of text files)
            $html = getCache($current);
            $should_cache = true;
            
            if (isset($html)) {
                //echo "Cache Hit.";
                $should_cache = false;  // No need to cache it if we already have it cached !
            } else {
                //echo "Cache Miss. Requesting.";
                $html = requestURL($current);
                $should_cache = true;   // Remember to cache it later so we don't have to keep requesting it!
            }
            
            if (isset($html)) {
                // We have the HTML content so we can pick it apart into its component pieces   
                $video = getMatch($REGEX_VIDEO, $html);
                $thumbnail = getMatch($REGEX_THUMBNAIL, $html);
                $episode = getMatch($REGEX_EPISODE, $thumbnail);
                $season_r = getMatch($REGEX_SEASON, $thumbnail);
                $next = getMatch($REGEX_NEXT, $html);
                
                output($season, $ep, $video, $thumbnail);
                
                if ($should_cache) {
                    setCache($current, $html);
                }
                
                // Very last step: set our $current for our next iteration
                $current = $next;
            } else {
                lawg(Log::ERR, "Unable to find content for URL.");
                // TODO: Should we keep trying in case of timeout or server error?
                $current = null;
            }  
            
            $ep += 1;
        }

        // If we've broken out of this loop then that means there is no "next" ... we need to make it up!
        lawg(Log::DEBUG, "Going on to next season");
        //$season = getMatch($REGEX_SEASON, $current);
        $season += 1;
        $current = getNextSeasonURL($season);

    } while (isset($current));
    
    lawg(Log::DEBUG, "Loop ended.");
    
    // =========================================
    // HELPER FUNCTIONS
    // =========================================
    
    function getCache($url) {
        $content = null;
        $filename = getFilename($url);
        if (isset($filename)) {
            try {
                // Knowingly suppressing the "no file found" warning because treating that case myself
                $content = @file_get_contents($filename);
                if (strlen($content) > 0) {
                    lawg(Log::DEBUG, "Successfully got content!");    
                } else {
                    //lawg(Log::DEBUG, "No content  =(");
                    $content = null;   
                }
            } catch (Exception $ex) {
                lawg(Log::ERR, "ERROR WHILE GETTING CACHE [$url]", $ex);
            }
        } else {
            lawg(Log::WARN, "Unable to open cache [$url]");
        }
        return $content;
    }
    
    function setCache($url, $content) {
        $filename = getFilename($url);
        if (isset($filename)) {
            try {
                $fh = fopen($filename, "w");
                fwrite($fh, $content);
                fclose($fh);
            } catch (Exception $ex) {
                lawg(Log::ERR, "ERROR WHILE SETTING CACHE [$filename]", $ex);
            }
        } else {
            lawg(Log::WARN, "Unable to open cache for URL [$url]");
        }
    }
        
    function getFilename($url) {
        global $CACHE_DIR;
        $filename = null;
        $slug = null;
        if (strlen($url) > 34) {
            $filename = substr($url, 34).".txt";    
        }
        if (isset($filename)) {
            $filename = "$CACHE_DIR/$filename";
        }
        return $filename;
    }
    
    function getMatch($regex, $str) {
        preg_match($regex, $str, $matches);
        $num_matches = count($matches);
        $match = null;
        if ($num_matches == 2) {
            $match = $matches[1];
        } // TODO: handle case where more than one match??
        return $match;
    }


    function requestURL($url) {
        // create curl resource 
        $ch = curl_init(); 

        // set url 
        curl_setopt($ch, CURLOPT_URL, $url); 

        //return the transfer as a string 
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1); 

        // $output contains the output string 
        $output = curl_exec($ch); 
        
        // see what the response code was
        $response = curl_getinfo($ch);
        
        // close curl resource to free up system resources 
        curl_close($ch);
        
        // make sure we didn't 404
        if ($response['http_code'] == 404) {
            $output = null;
        }
        
        return $output;
    }
    
    function getNextSeasonURL($season) {
        $base_url = "http://www.watchcartoononline.com/the-simpsons-season-".($season);
        $next_url = null;
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL,$base_url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 0);
        curl_exec($ch);
        $response = curl_getinfo($ch);           
        curl_close($ch);
        
        if ($response['http_code'] == 301 || $response['http_code'] == 302) {
            if ($headers = get_headers($response['url'])) {
                foreach ($headers as $value) {
                    if (substr(strtolower($value), 0, 9) == "location:") {
                        $next_url = trim(substr($value, 9));
                    }
                }
            }
        }
        
        lawg(Log::DEBUG, "Next current [$next_url]");
        return $next_url;
    }
    
    function lawg($level, $str, $ex = null) {
        if ($level <= Log::DEBUG) {
            print "$str\n";    
        }
    }
    
    function output($season, $episode, $video, $thumbnail) {
        $filename = "output_watchcartoononline.txt";
        try {
            $fh = fopen($filename, "a");
            fwrite($fh, "$season\t$episode\thttp://wwwstatic.megavideo.com/mv_player.swf?v=$video\t$thumbnail\n");
            fclose($fh);
        } catch (Exception $ex) {
            lawg(Log::ERR, "ERROR WHILE SETTING CACHE [$filename]", $ex);
        }
    }
    
?>